from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.modules.models import SpaceModule
from apps.spaces.models import Membership, Space
from apps.spaces.services import create_shared_space

from .models import WishItem
from .services import create_wish, update_wish


class WishModelAndServiceTests(APITestCase):
    def setUp(self):
        user_model = get_user_model()
        self.owner = user_model.objects.create_user(username="ana", password="secret")
        self.outsider = user_model.objects.create_user(username="marta", password="secret")
        self.space = create_shared_space(self.owner, "Casa")

    def test_create_normalizes_values_and_sets_defaults(self):
        wish = create_wish(
            self.owner,
            self.space,
            {
                "title": "  Curso de cerámica  ",
                "description": "  Un fin de semana  ",
                "currency": "eur",
                "price": Decimal("45.50"),
            },
        )

        self.assertEqual(wish.title, "Curso de cerámica")
        self.assertEqual(wish.description, "Un fin de semana")
        self.assertEqual(wish.currency, "EUR")
        self.assertEqual(wish.kind, WishItem.Kind.PRODUCT)
        self.assertEqual(wish.status, WishItem.Status.PENDING)
        self.assertEqual(wish.priority, WishItem.Priority.NORMAL)
        self.assertIsNone(wish.obtained_at)

    def test_obtained_timestamp_follows_status(self):
        wish = create_wish(self.owner, self.space, {"title": "Bicicleta"})

        wish = update_wish(wish, {"status": WishItem.Status.OBTAINED})
        self.assertIsNotNone(wish.obtained_at)

        wish = update_wish(wish, {"status": WishItem.Status.DISMISSED})
        self.assertIsNone(wish.obtained_at)

    def test_creator_must_belong_to_space(self):
        with self.assertRaises(DjangoValidationError):
            create_wish(self.outsider, self.space, {"title": "Ajeno"})

    def test_database_rejects_negative_price(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            WishItem.objects.bulk_create([
                WishItem(
                    space=self.space,
                    title="Imposible",
                    price=Decimal("-1.00"),
                    created_by=self.owner,
                )
            ])


class WishApiTests(APITestCase):
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
        self.list_url = reverse("wishlist:list", args=(self.space.id,))

    def create_api_wish(self, **overrides):
        self.client.force_authenticate(self.owner)
        response = self.client.post(
            self.list_url,
            {"title": "Curso de cerámica", **overrides},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return response

    def test_routes_require_authentication(self):
        self.assertEqual(
            self.client.get(self.list_url).status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_member_can_create_and_list_wish_with_optional_fields(self):
        self.client.force_authenticate(self.member)
        created = self.client.post(
            self.list_url,
            {
                "title": "Escapada rural",
                "kind": "experience",
                "priority": "high",
                "url": "https://example.com/escapada",
                "image_url": "https://example.com/image.jpg",
                "price": "120.00",
                "currency": "eur",
            },
            format="json",
        )
        listed = self.client.get(self.list_url)

        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        self.assertEqual(created.data["created_by"]["id"], self.member.id)
        self.assertEqual(created.data["currency"], "EUR")
        self.assertEqual(listed.status_code, status.HTTP_200_OK)
        self.assertEqual(len(listed.data["results"]), 1)
        self.assertEqual(listed.data["counts"]["pending"], 1)
        self.assertEqual(listed.data["counts"]["total"], 1)

    def test_patch_obtains_reopens_and_preserves_metadata(self):
        created = self.create_api_wish(
            kind="product",
            price="99.90",
            currency="EUR",
        )
        detail_url = reverse("wishlist:detail", args=(self.space.id, created.data["id"]))

        obtained = self.client.patch(detail_url, {"status": "obtained"}, format="json")
        reopened = self.client.patch(detail_url, {"status": "pending"}, format="json")

        self.assertEqual(obtained.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(obtained.data["obtained_at"])
        self.assertEqual(obtained.data["price"], "99.90")
        self.assertEqual(reopened.status_code, status.HTTP_200_OK)
        self.assertIsNone(reopened.data["obtained_at"])

    def test_filters_are_combined_and_counts_remain_global(self):
        target = self.create_api_wish(kind="idea", priority="high")
        self.create_api_wish(kind="product", priority="low", status="obtained")

        response = self.client.get(
            self.list_url,
            {"status": "pending", "kind": "idea", "priority": "high"},
        )

        self.assertEqual([wish["id"] for wish in response.data["results"]], [target.data["id"]])
        self.assertEqual(response.data["counts"]["pending"], 1)
        self.assertEqual(response.data["counts"]["obtained"], 1)
        self.assertEqual(response.data["counts"]["total"], 2)

    def test_urls_reject_unsafe_schemes_and_price_rejects_negative_values(self):
        self.client.force_authenticate(self.owner)

        unsafe = self.client.post(
            self.list_url,
            {"title": "Enlace", "url": "ftp://example.com/file"},
            format="json",
        )
        negative = self.client.post(
            self.list_url,
            {"title": "Precio", "price": "-0.01"},
            format="json",
        )

        self.assertEqual(unsafe.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(negative.status_code, status.HTTP_400_BAD_REQUEST)

    def test_other_space_wish_is_not_discoverable(self):
        other_wish = create_wish(
            self.outsider,
            self.other_space,
            {"title": "Privado"},
        )
        self.client.force_authenticate(self.owner)

        response = self.client.get(
            reverse("wishlist:detail", args=(self.space.id, other_wish.id))
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_outsider_and_disabled_module_are_blocked_without_data_loss(self):
        created = self.create_api_wish()
        detail_url = reverse("wishlist:detail", args=(self.space.id, created.data["id"]))

        self.client.force_authenticate(self.outsider)
        self.assertEqual(
            self.client.get(self.list_url).status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.client.force_authenticate(self.owner)
        SpaceModule.objects.filter(space=self.space, module_key="wishlist").update(
            enabled=False
        )
        self.assertEqual(
            self.client.patch(detail_url, {"title": "Oculto"}).status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.assertEqual(
            self.client.delete(detail_url).status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.assertTrue(WishItem.objects.filter(pk=created.data["id"]).exists())

    def test_delete_removes_wish(self):
        created = self.create_api_wish()

        response = self.client.delete(
            reverse("wishlist:detail", args=(self.space.id, created.data["id"]))
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(WishItem.objects.filter(pk=created.data["id"]).exists())
