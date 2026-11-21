from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.modules.models import SpaceModule
from apps.spaces.models import Membership, Space
from apps.spaces.services import create_shared_space

from .models import ShoppingItem, ShoppingList
from .services import (
    ShoppingOperationError,
    create_shopping_item,
    create_shopping_list,
    reorder_shopping_items,
    update_shopping_item,
)


class ShoppingModelAndServiceTests(APITestCase):
    def setUp(self):
        user_model = get_user_model()
        self.owner = user_model.objects.create_user(username="ana", password="secret")
        self.member = user_model.objects.create_user(username="luis", password="secret")
        self.outsider = user_model.objects.create_user(username="marta", password="secret")
        self.space = create_shared_space(self.owner, "Casa")
        Membership.objects.create(
            user=self.member,
            space=self.space,
            role=Membership.Role.MEMBER,
        )
        self.shopping_list = create_shopping_list(
            self.owner,
            self.space,
            {"name": " Supermercado "},
        )

    def test_list_and_item_are_trimmed_and_receive_defaults(self):
        item = create_shopping_item(
            self.member,
            self.shopping_list,
            {"name": " Leche ", "quantity": " 2 ", "unit": " uds "},
        )

        self.shopping_list.refresh_from_db()
        self.assertEqual(self.shopping_list.name, "Supermercado")
        self.assertEqual(item.name, "Leche")
        self.assertEqual(item.quantity, "2")
        self.assertEqual(item.unit, "uds")
        self.assertEqual(item.status, ShoppingItem.Status.PENDING)
        self.assertEqual(item.position, 0)
        self.assertIsNone(item.purchased_at)

    def test_purchase_timestamp_follows_status(self):
        item = create_shopping_item(
            self.owner,
            self.shopping_list,
            {"name": "Pan"},
        )

        item = update_shopping_item(item, {"status": ShoppingItem.Status.PURCHASED})
        self.assertIsNotNone(item.purchased_at)

        item = update_shopping_item(item, {"status": ShoppingItem.Status.PENDING})
        self.assertIsNone(item.purchased_at)

    def test_positions_are_unique_and_reordering_is_complete(self):
        first = create_shopping_item(
            self.owner, self.shopping_list, {"name": "Pan"}
        )
        second = create_shopping_item(
            self.owner, self.shopping_list, {"name": "Leche"}
        )

        reordered = reorder_shopping_items(
            self.shopping_list,
            [second.id, first.id],
        )

        self.assertEqual([item.id for item in reordered], [second.id, first.id])
        self.assertEqual(
            list(
                self.shopping_list.items.order_by("position").values_list(
                    "id", flat=True
                )
            ),
            [second.id, first.id],
        )
        with self.assertRaises(ShoppingOperationError):
            reorder_shopping_items(self.shopping_list, [first.id, first.id])

    def test_database_rejects_duplicate_position(self):
        create_shopping_item(self.owner, self.shopping_list, {"name": "Pan"})

        with self.assertRaises(IntegrityError), transaction.atomic():
            ShoppingItem.objects.bulk_create([
                ShoppingItem(
                    shopping_list=self.shopping_list,
                    name="Leche",
                    position=0,
                    created_by=self.owner,
                )
            ])

    def test_creator_must_belong_to_space(self):
        with self.assertRaises(DjangoValidationError):
            create_shopping_item(
                self.outsider,
                self.shopping_list,
                {"name": "Privado"},
            )


class ShoppingApiTests(APITestCase):
    def setUp(self):
        user_model = get_user_model()
        self.owner = user_model.objects.create_user(username="ana", password="secret")
        self.member = user_model.objects.create_user(username="luis", password="secret")
        self.outsider = user_model.objects.create_user(username="marta", password="secret")
        self.space = create_shared_space(self.owner, "Casa")
        self.other_space = Space.objects.get(
            created_by=self.outsider,
            kind=Space.Kind.PERSONAL,
        )
        Membership.objects.create(
            user=self.member,
            space=self.space,
            role=Membership.Role.MEMBER,
        )
        self.list_url = reverse("shopping:list", args=(self.space.id,))

    def create_api_list(self, name="Supermercado"):
        self.client.force_authenticate(self.owner)
        response = self.client.post(self.list_url, {"name": name}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return response

    def create_api_item(self, list_id, **overrides):
        payload = {"name": "Pan", **overrides}
        response = self.client.post(
            reverse("shopping:item-create", args=(self.space.id, list_id)),
            payload,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return response

    def test_routes_require_authentication(self):
        self.assertEqual(
            self.client.get(self.list_url).status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_member_can_create_list_and_items_and_read_summary(self):
        self.client.force_authenticate(self.member)
        created_list = self.client.post(
            self.list_url,
            {"name": "Mercado"},
            format="json",
        )
        created_item = self.create_api_item(
            created_list.data["id"],
            quantity="2",
            unit="uds",
            note="Integral",
        )
        listed = self.client.get(self.list_url)
        detail = self.client.get(
            reverse("shopping:detail", args=(self.space.id, created_list.data["id"]))
        )

        self.assertEqual(created_list.status_code, status.HTTP_201_CREATED)
        self.assertEqual(created_item.data["created_by"]["id"], self.member.id)
        self.assertEqual(listed.data[0]["pending_count"], 1)
        self.assertEqual(listed.data[0]["item_count"], 1)
        self.assertEqual(detail.data["items"][0]["note"], "Integral")

    def test_patch_marks_item_purchased_and_restores_it(self):
        shopping_list = self.create_api_list()
        item = self.create_api_item(shopping_list.data["id"])
        item_url = reverse(
            "shopping:item-detail",
            args=(self.space.id, shopping_list.data["id"], item.data["id"]),
        )

        purchased = self.client.patch(
            item_url,
            {"status": "purchased"},
            format="json",
        )
        restored = self.client.patch(
            item_url,
            {"status": "pending"},
            format="json",
        )

        self.assertEqual(purchased.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(purchased.data["purchased_at"])
        self.assertEqual(restored.status_code, status.HTTP_200_OK)
        self.assertIsNone(restored.data["purchased_at"])

    def test_detail_filters_items_without_changing_totals(self):
        shopping_list = self.create_api_list()
        pending = self.create_api_item(shopping_list.data["id"], name="Pan")
        purchased = self.create_api_item(
            shopping_list.data["id"],
            name="Leche",
            status="purchased",
        )
        detail_url = reverse(
            "shopping:detail",
            args=(self.space.id, shopping_list.data["id"]),
        )

        response = self.client.get(detail_url, {"status": "purchased"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([item["id"] for item in response.data["items"]], [purchased.data["id"]])
        self.assertEqual(response.data["pending_count"], 1)
        self.assertEqual(response.data["purchased_count"], 1)
        self.assertNotEqual(pending.data["id"], purchased.data["id"])

    def test_reorder_rejects_missing_duplicate_and_foreign_items(self):
        shopping_list = self.create_api_list()
        first = self.create_api_item(shopping_list.data["id"], name="Pan")
        second = self.create_api_item(shopping_list.data["id"], name="Leche")
        other_list = self.create_api_list("Otra")
        foreign = self.create_api_item(other_list.data["id"], name="Café")
        reorder_url = reverse(
            "shopping:item-reorder",
            args=(self.space.id, shopping_list.data["id"]),
        )

        valid = self.client.post(
            reorder_url,
            {"item_ids": [second.data["id"], first.data["id"]]},
            format="json",
        )
        missing = self.client.post(
            reorder_url,
            {"item_ids": [first.data["id"]]},
            format="json",
        )
        duplicate = self.client.post(
            reorder_url,
            {"item_ids": [first.data["id"], first.data["id"]]},
            format="json",
        )
        foreign_item = self.client.post(
            reorder_url,
            {"item_ids": [first.data["id"], foreign.data["id"]]},
            format="json",
        )

        self.assertEqual(valid.status_code, status.HTTP_200_OK)
        self.assertEqual(
            [item["id"] for item in valid.data],
            [second.data["id"], first.data["id"]],
        )
        self.assertEqual(missing.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(duplicate.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(foreign_item.status_code, status.HTTP_400_BAD_REQUEST)

    def test_other_space_ids_are_not_discoverable(self):
        other_list = create_shopping_list(
            self.outsider,
            self.other_space,
            {"name": "Privada"},
        )
        other_item = create_shopping_item(
            self.outsider,
            other_list,
            {"name": "Secreto"},
        )
        self.client.force_authenticate(self.owner)

        list_response = self.client.get(
            reverse("shopping:detail", args=(self.space.id, other_list.id))
        )
        item_response = self.client.patch(
            reverse(
                "shopping:item-detail",
                args=(self.space.id, other_list.id, other_item.id),
            ),
            {"name": "Visible"},
            format="json",
        )

        self.assertEqual(list_response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(item_response.status_code, status.HTTP_404_NOT_FOUND)

    def test_outsider_and_disabled_module_are_blocked_without_data_loss(self):
        shopping_list = self.create_api_list()
        list_id = shopping_list.data["id"]
        detail_url = reverse("shopping:detail", args=(self.space.id, list_id))

        self.client.force_authenticate(self.outsider)
        self.assertEqual(
            self.client.get(self.list_url).status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.client.force_authenticate(self.owner)
        SpaceModule.objects.filter(space=self.space, module_key="shopping").update(
            enabled=False
        )
        self.assertEqual(
            self.client.get(detail_url).status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.assertEqual(
            self.client.delete(detail_url).status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.assertTrue(ShoppingList.objects.filter(pk=list_id).exists())

    def test_deleting_list_cascades_items(self):
        shopping_list = self.create_api_list()
        self.create_api_item(shopping_list.data["id"])

        response = self.client.delete(
            reverse("shopping:detail", args=(self.space.id, shopping_list.data["id"]))
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(ShoppingItem.objects.exists())
