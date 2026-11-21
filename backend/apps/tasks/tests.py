from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.modules.models import SpaceModule
from apps.spaces.models import Membership, Space
from apps.spaces.services import create_shared_space, remove_member

from .models import Task, TaskAssignment
from .services import TaskOperationError, create_task, update_task


class TaskModelAndServiceTests(APITestCase):
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

    def test_create_task_sets_defaults_and_assignments(self):
        task = create_task(
            self.owner,
            self.space,
            {"title": "  Comprar pan  ", "assignee_ids": [self.member.id]},
        )

        self.assertEqual(task.title, "Comprar pan")
        self.assertEqual(task.status, Task.Status.PENDING)
        self.assertEqual(task.priority, Task.Priority.NORMAL)
        self.assertIsNone(task.completed_at)
        self.assertEqual(list(task.assignees.all()), [self.member])

    def test_completed_at_follows_status(self):
        task = create_task(self.owner, self.space, {"title": "Regar plantas"})

        task = update_task(task, {"status": Task.Status.COMPLETED})
        self.assertIsNotNone(task.completed_at)

        task = update_task(task, {"status": Task.Status.PENDING})
        self.assertIsNone(task.completed_at)

    def test_assignment_requires_membership_and_is_atomic(self):
        task = create_task(
            self.owner,
            self.space,
            {"title": "Ordenar", "assignee_ids": [self.member.id]},
        )

        with self.assertRaises(TaskOperationError):
            update_task(task, {"assignee_ids": [self.owner.id, self.outsider.id]})

        self.assertEqual(list(task.assignees.all()), [self.member])

    def test_assignment_is_unique(self):
        task = create_task(self.owner, self.space, {"title": "Ordenar"})
        TaskAssignment.objects.create(task=task, user=self.member)

        with self.assertRaises(IntegrityError), transaction.atomic():
            TaskAssignment.objects.bulk_create(
                [TaskAssignment(task=task, user=self.member)]
            )

    def test_removing_member_clears_their_assignments(self):
        task = create_task(
            self.owner,
            self.space,
            {"title": "Ordenar", "assignee_ids": [self.member.id]},
        )

        remove_member(self.space, self.owner, self.member.id)

        self.assertFalse(task.assignments.exists())


class TaskApiTests(APITestCase):
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
        self.list_url = reverse("tasks:list", args=(self.space.id,))

    def create_api_task(self, **overrides):
        payload = {"title": "Comprar pan", **overrides}
        self.client.force_authenticate(self.owner)
        response = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return response

    def test_routes_require_authentication(self):
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_member_can_create_and_list_task_with_multiple_assignees(self):
        self.client.force_authenticate(self.member)

        created = self.client.post(
            self.list_url,
            {
                "title": "Preparar la cena",
                "priority": "high",
                "assignee_ids": [self.owner.id, self.member.id],
            },
            format="json",
        )
        listed = self.client.get(self.list_url)

        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        self.assertEqual(created.data["created_by"]["id"], self.member.id)
        self.assertEqual(
            {user["id"] for user in created.data["assignees"]},
            {self.owner.id, self.member.id},
        )
        self.assertEqual(listed.status_code, status.HTTP_200_OK)
        self.assertEqual(len(listed.data), 1)

    def test_outsider_cannot_discover_space_tasks(self):
        response = self.create_api_task()
        task_id = response.data["id"]
        self.client.force_authenticate(self.outsider)

        listed = self.client.get(self.list_url)
        detailed = self.client.get(reverse("tasks:detail", args=(self.space.id, task_id)))

        self.assertEqual(listed.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(detailed.status_code, status.HTTP_403_FORBIDDEN)

    def test_task_id_from_another_space_returns_not_found(self):
        other_task = create_task(self.outsider, self.other_space, {"title": "Privada"})
        self.client.force_authenticate(self.owner)

        response = self.client.get(
            reverse("tasks:detail", args=(self.space.id, other_task.id))
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_cannot_assign_outsider(self):
        self.client.force_authenticate(self.owner)

        response = self.client.post(
            self.list_url,
            {"title": "Tarea", "assignee_ids": [self.outsider.id]},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Task.objects.filter(space=self.space).count(), 0)

    def test_patch_completes_reopens_and_updates_assignments(self):
        created = self.create_api_task(assignee_ids=[self.member.id])
        detail_url = reverse("tasks:detail", args=(self.space.id, created.data["id"]))

        completed = self.client.patch(
            detail_url,
            {"status": "completed", "assignee_ids": [self.owner.id]},
            format="json",
        )
        reopened = self.client.patch(detail_url, {"status": "pending"}, format="json")

        self.assertEqual(completed.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(completed.data["completed_at"])
        self.assertEqual(completed.data["assignees"][0]["id"], self.owner.id)
        self.assertEqual(reopened.status_code, status.HTTP_200_OK)
        self.assertIsNone(reopened.data["completed_at"])

    def test_delete_removes_task_and_assignments(self):
        created = self.create_api_task(assignee_ids=[self.member.id])
        detail_url = reverse("tasks:detail", args=(self.space.id, created.data["id"]))

        response = self.client.delete(detail_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Task.objects.filter(pk=created.data["id"]).exists())
        self.assertFalse(TaskAssignment.objects.exists())

    def test_disabled_module_blocks_every_operation_without_deleting_data(self):
        created = self.create_api_task()
        detail_url = reverse("tasks:detail", args=(self.space.id, created.data["id"]))
        SpaceModule.objects.filter(space=self.space, module_key="tasks").update(
            enabled=False
        )

        listed = self.client.get(self.list_url)
        updated = self.client.patch(detail_url, {"title": "Oculta"}, format="json")
        deleted = self.client.delete(detail_url)

        self.assertEqual(listed.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(updated.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(deleted.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Task.objects.filter(pk=created.data["id"]).exists())

    def test_filters_by_status_assignee_and_due_date(self):
        today = timezone.localdate()
        pending = self.create_api_task(
            title="Vencida",
            due_date=(today - timedelta(days=1)).isoformat(),
            assignee_ids=[self.member.id],
        )
        self.create_api_task(title="Sin fecha", status="completed")

        overdue = self.client.get(self.list_url, {"due": "overdue"})
        assigned = self.client.get(self.list_url, {"assigned_to": self.member.id})
        completed = self.client.get(self.list_url, {"status": "completed"})

        self.assertEqual([task["id"] for task in overdue.data], [pending.data["id"]])
        self.assertEqual([task["id"] for task in assigned.data], [pending.data["id"]])
        self.assertEqual(len(completed.data), 1)
        self.assertEqual(completed.data[0]["title"], "Sin fecha")

    def test_personal_space_supports_unassigned_tasks(self):
        personal = Space.objects.get(
            created_by=self.owner,
            kind=Space.Kind.PERSONAL,
        )
        self.client.force_authenticate(self.owner)

        response = self.client.post(
            reverse("tasks:list", args=(personal.id,)),
            {"title": "Tarea privada"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["assignees"], [])
