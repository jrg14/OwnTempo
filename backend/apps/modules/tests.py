from dataclasses import replace
from io import StringIO
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.spaces.models import Membership, Space
from apps.spaces.services import create_shared_space

from .catalog import MODULE_KEYS, get_module_definition
from .models import SpaceModule
from .permissions import HasActiveModule


class ModuleCatalogTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="ana",
            password="secret",
        )

    def test_catalog_requires_authentication(self):
        response = self.client.get(reverse("modules:catalog"))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_catalog_contains_exactly_the_five_initial_modules(self):
        self.client.force_authenticate(self.user)

        response = self.client.get(reverse("modules:catalog"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            tuple(module["key"] for module in response.data),
            MODULE_KEYS,
        )
        availability = {module["key"]: module["available"] for module in response.data}
        self.assertTrue(availability["tasks"])
        self.assertTrue(availability["shopping"])
        self.assertTrue(availability["wishlist"])
        self.assertTrue(availability["calendar"])
        self.assertTrue(all(
            not available
            for key, available in availability.items()
            if key not in {"tasks", "shopping", "wishlist", "calendar"}
        ))


class SpaceModuleModelTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="ana",
            password="secret",
        )
        self.personal_space = Space.objects.get(
            created_by=self.user,
            kind=Space.Kind.PERSONAL,
        )

    def test_personal_space_receives_all_module_configurations(self):
        configurations = SpaceModule.objects.filter(space=self.personal_space)

        self.assertEqual(configurations.count(), len(MODULE_KEYS))
        self.assertEqual(
            tuple(configurations.values_list("module_key", flat=True)),
            MODULE_KEYS,
        )
        self.assertTrue(all(config.enabled for config in configurations))

    def test_shared_space_receives_all_module_configurations(self):
        space = create_shared_space(self.user, "Casa")

        self.assertEqual(
            SpaceModule.objects.filter(space=space).count(),
            len(MODULE_KEYS),
        )

    def test_space_and_module_key_are_unique(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            SpaceModule.objects.create(
                space=self.personal_space,
                module_key=MODULE_KEYS[0],
            )

    def test_database_rejects_unknown_module_key(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            SpaceModule.objects.create(
                space=self.personal_space,
                module_key="unknown",
            )

    def test_management_command_repairs_missing_configurations_idempotently(self):
        SpaceModule.objects.filter(
            space=self.personal_space,
            module_key="wishlist",
        ).delete()
        first_output = StringIO()
        second_output = StringIO()

        call_command("ensure_space_modules", stdout=first_output)
        call_command("ensure_space_modules", stdout=second_output)

        self.assertEqual(
            SpaceModule.objects.filter(space=self.personal_space).count(),
            len(MODULE_KEYS),
        )
        self.assertIn("Configuraciones de módulos creadas: 1", first_output.getvalue())
        self.assertIn("Configuraciones de módulos creadas: 0", second_output.getvalue())


class SpaceModuleApiTests(APITestCase):
    def setUp(self):
        user_model = get_user_model()
        self.owner = user_model.objects.create_user(
            username="ana",
            password="secret",
        )
        self.member = user_model.objects.create_user(
            username="luis",
            password="secret",
        )
        self.outsider = user_model.objects.create_user(
            username="marta",
            password="secret",
        )
        self.space = create_shared_space(self.owner, "Casa")
        Membership.objects.create(
            user=self.member,
            space=self.space,
            role=Membership.Role.MEMBER,
        )

    def test_member_can_list_space_modules(self):
        self.client.force_authenticate(self.member)

        response = self.client.get(
            reverse("modules:space-module-list", args=(self.space.id,))
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(tuple(item["key"] for item in response.data), MODULE_KEYS)
        self.assertTrue(all(item["enabled"] for item in response.data))
        availability = {item["key"]: item["available"] for item in response.data}
        self.assertTrue(availability["tasks"])
        self.assertTrue(availability["shopping"])
        self.assertTrue(availability["wishlist"])
        self.assertTrue(availability["calendar"])
        self.assertTrue(all(
            not available
            for key, available in availability.items()
            if key not in {"tasks", "shopping", "wishlist", "calendar"}
        ))

    def test_outsider_cannot_list_space_modules(self):
        self.client.force_authenticate(self.outsider)

        response = self.client.get(
            reverse("modules:space-module-list", args=(self.space.id,))
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_owner_can_disable_module(self):
        self.client.force_authenticate(self.owner)

        response = self.client.patch(
            reverse(
                "modules:space-module-update",
                args=(self.space.id, "tasks"),
            ),
            {"enabled": False},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["enabled"])
        self.assertFalse(
            SpaceModule.objects.get(space=self.space, module_key="tasks").enabled
        )

    def test_member_cannot_change_module_configuration(self):
        self.client.force_authenticate(self.member)

        response = self.client.patch(
            reverse(
                "modules:space-module-update",
                args=(self.space.id, "tasks"),
            ),
            {"enabled": False},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(
            SpaceModule.objects.get(space=self.space, module_key="tasks").enabled
        )

    def test_unknown_module_is_not_created(self):
        self.client.force_authenticate(self.owner)

        response = self.client.patch(
            reverse(
                "modules:space-module-update",
                args=(self.space.id, "unknown"),
            ),
            {"enabled": True},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(
            SpaceModule.objects.filter(
                space=self.space,
                module_key="unknown",
            ).exists()
        )

    def test_configurations_are_independent_between_spaces(self):
        other_space = create_shared_space(self.owner, "Viaje")
        SpaceModule.objects.filter(space=self.space, module_key="expenses").update(
            enabled=False
        )

        self.assertFalse(
            SpaceModule.objects.get(space=self.space, module_key="expenses").enabled
        )
        self.assertTrue(
            SpaceModule.objects.get(space=other_space, module_key="expenses").enabled
        )


class ActiveModulePermissionTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="ana",
            password="secret",
        )
        self.space = Space.objects.get(
            created_by=self.user,
            kind=Space.Kind.PERSONAL,
        )
        self.view = SimpleNamespace(
            kwargs={"space_id": self.space.id, "module_key": "shopping"}
        )

    def test_unavailable_module_is_rejected_even_when_enabled(self):
        self.view.kwargs["module_key"] = "expenses"
        self.assertFalse(HasActiveModule().has_permission(None, self.view))

    def test_available_module_must_also_be_enabled(self):
        self.view.kwargs["module_key"] = "tasks"
        available_definition = replace(get_module_definition("tasks"), available=True)

        with patch(
            "apps.modules.permissions.get_module_definition",
            return_value=available_definition,
        ):
            self.assertTrue(HasActiveModule().has_permission(None, self.view))
            SpaceModule.objects.filter(
                space=self.space,
                module_key="tasks",
            ).update(enabled=False)
            self.assertFalse(HasActiveModule().has_permission(None, self.view))
