from datetime import date, datetime, timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.modules.models import SpaceModule
from apps.spaces.models import Membership, Space
from apps.spaces.services import create_shared_space

from .models import CalendarEvent
from .services import create_event, update_event


class CalendarModelAndServiceTests(APITestCase):
    def setUp(self):
        user_model = get_user_model()
        self.owner = user_model.objects.create_user(username="ana", password="secret")
        self.outsider = user_model.objects.create_user(username="marta", password="secret")
        self.space = create_shared_space(self.owner, "Casa")
        self.start = timezone.make_aware(datetime(2026, 11, 24, 17, 0))
        self.end = self.start + timedelta(hours=1)

    def test_timed_event_is_trimmed_and_timezone_aware(self):
        event = create_event(
            self.owner,
            self.space,
            {
                "title": "  Revisión  ",
                "description": "  Preparar decisiones  ",
                "start_at": self.start,
                "end_at": self.end,
                "all_day": False,
            },
        )

        self.assertEqual(event.title, "Revisión")
        self.assertEqual(event.description, "Preparar decisiones")
        self.assertTrue(timezone.is_aware(event.start_at))
        self.assertIsNone(event.date)

    def test_all_day_event_uses_date_without_times(self):
        event = create_event(
            self.owner,
            self.space,
            {"title": "Festivo", "all_day": True, "date": date(2026, 12, 6)},
        )

        self.assertEqual(event.date, date(2026, 12, 6))
        self.assertIsNone(event.start_at)
        self.assertIsNone(event.end_at)

    def test_end_must_be_after_start(self):
        with self.assertRaises(DjangoValidationError):
            create_event(
                self.owner,
                self.space,
                {
                    "title": "Inválido",
                    "start_at": self.start,
                    "end_at": self.start,
                    "all_day": False,
                },
            )

    def test_switching_modes_clears_incompatible_fields(self):
        event = create_event(
            self.owner,
            self.space,
            {
                "title": "Revisión",
                "start_at": self.start,
                "end_at": self.end,
                "all_day": False,
            },
        )

        event = update_event(
            event,
            {"all_day": True, "date": date(2026, 11, 25)},
        )

        self.assertTrue(event.all_day)
        self.assertIsNone(event.start_at)
        self.assertIsNone(event.end_at)

    def test_creator_must_belong_to_space(self):
        with self.assertRaises(DjangoValidationError):
            create_event(
                self.outsider,
                self.space,
                {
                    "title": "Ajeno",
                    "start_at": self.start,
                    "end_at": self.end,
                    "all_day": False,
                },
            )


class CalendarApiTests(APITestCase):
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
        self.list_url = reverse("calendar:event-list", args=(self.space.id,))
        self.range = {"from": "2026-11-01", "to": "2026-11-30"}

    def create_timed_event(self, **overrides):
        self.client.force_authenticate(self.owner)
        payload = {
            "title": "Revisión",
            "start_at": "2026-11-24T17:00:00+01:00",
            "end_at": "2026-11-24T18:00:00+01:00",
            "all_day": False,
            **overrides,
        }
        response = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return response

    def test_list_requires_authentication_and_range(self):
        self.assertEqual(
            self.client.get(self.list_url, self.range).status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.client.force_authenticate(self.owner)
        self.assertEqual(
            self.client.get(self.list_url).status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_member_can_create_timed_and_all_day_events(self):
        self.client.force_authenticate(self.member)
        timed = self.client.post(
            self.list_url,
            {
                "title": "Cena",
                "start_at": "2026-11-24T20:00:00+01:00",
                "end_at": "2026-11-24T22:00:00+01:00",
                "all_day": False,
                "color": "rose",
            },
            format="json",
        )
        all_day = self.client.post(
            self.list_url,
            {"title": "Festivo", "date": "2026-11-25", "all_day": True},
            format="json",
        )

        self.assertEqual(timed.status_code, status.HTTP_201_CREATED)
        self.assertEqual(timed.data["created_by"]["id"], self.member.id)
        self.assertEqual(all_day.status_code, status.HTTP_201_CREATED)
        self.assertIsNone(all_day.data["start_at"])

    def test_range_includes_overlapping_event(self):
        event = self.create_timed_event(
            start_at="2026-10-31T23:30:00+01:00",
            end_at="2026-11-01T01:30:00+01:00",
        )

        response = self.client.get(
            self.list_url,
            {"from": "2026-11-01", "to": "2026-11-01"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([item["id"] for item in response.data], [event.data["id"]])

    def test_range_rejects_invalid_and_excessive_values(self):
        self.client.force_authenticate(self.owner)

        reversed_range = self.client.get(
            self.list_url, {"from": "2026-11-30", "to": "2026-11-01"}
        )
        excessive = self.client.get(
            self.list_url, {"from": "2026-01-01", "to": "2026-05-01"}
        )

        self.assertEqual(reversed_range.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(excessive.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_switches_to_all_day_and_delete_removes_event(self):
        created = self.create_timed_event()
        detail_url = reverse(
            "calendar:event-detail", args=(self.space.id, created.data["id"])
        )

        updated = self.client.patch(
            detail_url,
            {"all_day": True, "date": "2026-11-25"},
            format="json",
        )
        deleted = self.client.delete(detail_url)

        self.assertEqual(updated.status_code, status.HTTP_200_OK)
        self.assertTrue(updated.data["all_day"])
        self.assertIsNone(updated.data["start_at"])
        self.assertEqual(deleted.status_code, status.HTTP_204_NO_CONTENT)

    def test_event_from_other_space_is_not_discoverable(self):
        other_event = create_event(
            self.outsider,
            self.other_space,
            {
                "title": "Privado",
                "all_day": True,
                "date": date(2026, 11, 20),
            },
        )
        self.client.force_authenticate(self.owner)

        response = self.client.get(
            reverse("calendar:event-detail", args=(self.space.id, other_event.id))
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_disabled_module_blocks_operations_without_deleting_data(self):
        created = self.create_timed_event()
        detail_url = reverse(
            "calendar:event-detail", args=(self.space.id, created.data["id"])
        )
        SpaceModule.objects.filter(space=self.space, module_key="calendar").update(
            enabled=False
        )

        listed = self.client.get(self.list_url, self.range)
        updated = self.client.patch(detail_url, {"title": "Oculto"}, format="json")
        deleted = self.client.delete(detail_url)

        self.assertEqual(listed.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(updated.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(deleted.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(CalendarEvent.objects.filter(pk=created.data["id"]).exists())
