from io import StringIO

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Membership, Space


class PersonalSpaceModelTests(APITestCase):
    def setUp(self):
        self.user_model = get_user_model()

    def test_new_user_receives_one_personal_space(self):
        user = self.user_model.objects.create_user(username="ana", password="secret")

        space = Space.objects.get(created_by=user, kind=Space.Kind.PERSONAL)
        membership = Membership.objects.get(space=space)

        self.assertEqual(space.name, "Mi espacio")
        self.assertEqual(membership.user, user)
        self.assertEqual(membership.role, Membership.Role.OWNER)

    def test_personal_space_is_not_duplicated_when_user_is_updated(self):
        user = self.user_model.objects.create_user(username="ana", password="secret")

        user.first_name = "Ana"
        user.save()

        self.assertEqual(
            Space.objects.filter(
                created_by=user,
                kind=Space.Kind.PERSONAL,
            ).count(),
            1,
        )

    def test_database_rejects_second_personal_space_for_same_user(self):
        user = self.user_model.objects.create_user(username="ana", password="secret")

        with self.assertRaises(IntegrityError), transaction.atomic():
            Space.objects.create(
                name="Otro espacio",
                kind=Space.Kind.PERSONAL,
                created_by=user,
            )

    def test_personal_space_rejects_another_member(self):
        owner = self.user_model.objects.create_user(username="ana", password="secret")
        other_user = self.user_model.objects.create_user(
            username="luis",
            password="secret",
        )
        space = Space.objects.get(created_by=owner, kind=Space.Kind.PERSONAL)

        with self.assertRaises(ValidationError):
            Membership.objects.create(
                user=other_user,
                space=space,
                role=Membership.Role.MEMBER,
            )

    def test_management_command_repairs_missing_personal_space(self):
        user = self.user_model.objects.create_user(username="ana", password="secret")
        Space.objects.get(created_by=user, kind=Space.Kind.PERSONAL).delete()
        output = StringIO()

        call_command("ensure_personal_spaces", stdout=output)

        self.assertTrue(
            Space.objects.filter(created_by=user, kind=Space.Kind.PERSONAL).exists()
        )
        self.assertIn("Espacios personales creados: 1", output.getvalue())


class PersonalSpaceApiTests(APITestCase):
    def setUp(self):
        user_model = get_user_model()
        self.ana = user_model.objects.create_user(username="ana", password="secret")
        self.luis = user_model.objects.create_user(username="luis", password="secret")
        self.ana_space = Space.objects.get(
            created_by=self.ana,
            kind=Space.Kind.PERSONAL,
        )
        self.luis_space = Space.objects.get(
            created_by=self.luis,
            kind=Space.Kind.PERSONAL,
        )

    def test_routes_require_authentication(self):
        personal_response = self.client.get(reverse("spaces:personal"))
        list_response = self.client.get(reverse("spaces:list"))

        self.assertEqual(personal_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(list_response.status_code, status.HTTP_403_FORBIDDEN)

    def test_personal_route_returns_current_users_space(self):
        self.client.force_authenticate(self.ana)

        response = self.client.get(reverse("spaces:personal"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.ana_space.id)
        self.assertEqual(response.data["kind"], Space.Kind.PERSONAL)
        self.assertEqual(response.data["role"], Membership.Role.OWNER)

    def test_user_can_rename_only_their_personal_space(self):
        self.client.force_authenticate(self.ana)

        response = self.client.patch(
            reverse("spaces:personal"),
            {"name": "Privado de Ana"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.ana_space.refresh_from_db()
        self.luis_space.refresh_from_db()
        self.assertEqual(self.ana_space.name, "Privado de Ana")
        self.assertEqual(self.luis_space.name, "Mi espacio")

    def test_personal_space_name_cannot_be_empty(self):
        self.client.force_authenticate(self.ana)

        response = self.client.patch(
            reverse("spaces:personal"),
            {"name": "   "},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["name"][0],
            "El nombre del espacio no puede estar vacío.",
        )

    def test_space_list_only_contains_accessible_spaces(self):
        shared_space = Space.objects.create(
            name="Casa",
            kind=Space.Kind.SHARED,
            created_by=self.ana,
        )
        Membership.objects.create(
            user=self.ana,
            space=shared_space,
            role=Membership.Role.OWNER,
        )
        self.client.force_authenticate(self.ana)

        response = self.client.get(reverse("spaces:list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        returned_ids = {space["id"] for space in response.data}
        self.assertEqual(returned_ids, {self.ana_space.id, shared_space.id})
        self.assertNotIn(self.luis_space.id, returned_ids)
