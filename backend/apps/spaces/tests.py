from io import StringIO

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Invitation, Membership, Space


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


class SharedSpaceApiTests(APITestCase):
    def setUp(self):
        user_model = get_user_model()
        self.ana = user_model.objects.create_user(
            username="ana",
            first_name="Ana",
            password="secret",
        )
        self.luis = user_model.objects.create_user(
            username="luis",
            first_name="Luis",
            password="secret",
        )
        self.marta = user_model.objects.create_user(
            username="marta",
            first_name="Marta",
            password="secret",
        )
        self.client.force_authenticate(self.ana)

    def create_shared_space(self, name="Casa"):
        response = self.client.post(
            reverse("spaces:list"),
            {"name": name},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return Space.objects.get(pk=response.data["id"])

    def invite(self, space, username="luis"):
        return self.client.post(
            reverse("spaces:invitation-list", args=(space.id,)),
            {"username": username},
            format="json",
        )

    def test_creating_shared_space_creates_owner_membership(self):
        space = self.create_shared_space("  Casa  ")

        membership = Membership.objects.get(space=space, user=self.ana)
        self.assertEqual(space.name, "Casa")
        self.assertEqual(space.kind, Space.Kind.SHARED)
        self.assertEqual(membership.role, Membership.Role.OWNER)

    def test_owner_can_rename_shared_space(self):
        space = self.create_shared_space()

        response = self.client.patch(
            reverse("spaces:detail", args=(space.id,)),
            {"name": "Nuestro hogar"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        space.refresh_from_db()
        self.assertEqual(space.name, "Nuestro hogar")

    def test_invitation_acceptance_grants_access(self):
        space = self.create_shared_space()
        invitation_response = self.invite(space)
        self.assertEqual(invitation_response.status_code, status.HTTP_201_CREATED)
        invitation_id = invitation_response.data["id"]

        self.client.force_authenticate(self.luis)
        spaces_before = self.client.get(reverse("spaces:list"))
        received = self.client.get(reverse("spaces:received-invitations"))
        accept = self.client.post(
            reverse("spaces:invitation-accept", args=(invitation_id,)),
            format="json",
        )
        spaces_after = self.client.get(reverse("spaces:list"))

        self.assertNotIn(space.id, {item["id"] for item in spaces_before.data})
        self.assertEqual([item["id"] for item in received.data], [invitation_id])
        self.assertEqual(accept.status_code, status.HTTP_200_OK)
        self.assertIn(space.id, {item["id"] for item in spaces_after.data})
        self.assertTrue(
            Membership.objects.filter(
                space=space,
                user=self.luis,
                role=Membership.Role.MEMBER,
            ).exists()
        )

    def test_rejected_invitation_does_not_grant_access(self):
        space = self.create_shared_space()
        invitation_id = self.invite(space).data["id"]
        self.client.force_authenticate(self.luis)

        response = self.client.post(
            reverse("spaces:invitation-reject", args=(invitation_id,)),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(Membership.objects.filter(space=space, user=self.luis).exists())
        invitation = Invitation.objects.get(pk=invitation_id)
        self.assertEqual(invitation.status, Invitation.Status.REJECTED)
        self.assertIsNotNone(invitation.responded_at)

    def test_duplicate_pending_invitation_is_rejected(self):
        space = self.create_shared_space()
        first = self.invite(space)
        second = self.invite(space)

        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            second.data["detail"],
            "El usuario ya tiene una invitación pendiente.",
        )

    def test_owner_can_cancel_pending_invitation(self):
        space = self.create_shared_space()
        invitation_id = self.invite(space).data["id"]

        response = self.client.delete(
            reverse("spaces:invitation-cancel", args=(space.id, invitation_id))
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        invitation = Invitation.objects.get(pk=invitation_id)
        self.assertEqual(invitation.status, Invitation.Status.CANCELLED)

        self.client.force_authenticate(self.luis)
        accept = self.client.post(
            reverse("spaces:invitation-accept", args=(invitation_id,)),
            format="json",
        )
        self.assertEqual(accept.status_code, status.HTTP_400_BAD_REQUEST)

    def test_member_cannot_manage_space_or_invitations(self):
        space = self.create_shared_space()
        Membership.objects.create(
            space=space,
            user=self.luis,
            role=Membership.Role.MEMBER,
        )
        self.client.force_authenticate(self.luis)

        rename = self.client.patch(
            reverse("spaces:detail", args=(space.id,)),
            {"name": "Nombre ajeno"},
            format="json",
        )
        invite = self.invite(space, "marta")
        remove = self.client.delete(
            reverse("spaces:member-remove", args=(space.id, self.ana.id))
        )

        self.assertEqual(rename.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(invite.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(remove.status_code, status.HTTP_403_FORBIDDEN)

    def test_outsider_cannot_discover_space_details_or_members(self):
        space = self.create_shared_space()
        self.client.force_authenticate(self.marta)

        detail = self.client.get(reverse("spaces:detail", args=(space.id,)))
        members = self.client.get(reverse("spaces:member-list", args=(space.id,)))

        self.assertEqual(detail.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(members.status_code, status.HTTP_403_FORBIDDEN)

    def test_only_invited_user_can_respond(self):
        space = self.create_shared_space()
        invitation_id = self.invite(space).data["id"]
        self.client.force_authenticate(self.marta)

        response = self.client.post(
            reverse("spaces:invitation-accept", args=(invitation_id,)),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(Membership.objects.filter(space=space, user=self.marta).exists())

    def test_owner_can_remove_member(self):
        space = self.create_shared_space()
        Membership.objects.create(
            space=space,
            user=self.luis,
            role=Membership.Role.MEMBER,
        )

        response = self.client.delete(
            reverse("spaces:member-remove", args=(space.id, self.luis.id))
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Membership.objects.filter(space=space, user=self.luis).exists())

        self.client.force_authenticate(self.luis)
        detail = self.client.get(reverse("spaces:detail", args=(space.id,)))
        self.assertEqual(detail.status_code, status.HTTP_403_FORBIDDEN)

    def test_member_can_leave_but_owner_cannot(self):
        space = self.create_shared_space()
        Membership.objects.create(
            space=space,
            user=self.luis,
            role=Membership.Role.MEMBER,
        )

        owner_response = self.client.post(
            reverse("spaces:leave", args=(space.id,)),
            format="json",
        )
        self.client.force_authenticate(self.luis)
        member_response = self.client.post(
            reverse("spaces:leave", args=(space.id,)),
            format="json",
        )

        self.assertEqual(owner_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(member_response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertTrue(Membership.objects.filter(space=space, user=self.ana).exists())
        self.assertFalse(Membership.objects.filter(space=space, user=self.luis).exists())
