from django.db import transaction
from django.utils import timezone

from apps.spaces.models import Membership

from .models import Task, TaskAssignment


class TaskOperationError(Exception):
    pass


def _validated_assignee_ids(space, user_ids):
    assignee_ids = tuple(dict.fromkeys(user_ids))
    member_ids = set(
        Membership.objects.filter(
            space=space,
            user_id__in=assignee_ids,
        ).values_list("user_id", flat=True)
    )
    if member_ids != set(assignee_ids):
        raise TaskOperationError(
            "Todos los responsables deben pertenecer al espacio."
        )
    return assignee_ids


def _apply_status(task, status):
    task.status = status
    if status == Task.Status.COMPLETED:
        task.completed_at = task.completed_at or timezone.now()
    else:
        task.completed_at = None


def set_task_assignees(task, user_ids):
    assignee_ids = _validated_assignee_ids(task.space, user_ids)
    task.assignments.all().delete()
    TaskAssignment.objects.bulk_create(
        TaskAssignment(task=task, user_id=user_id) for user_id in assignee_ids
    )


@transaction.atomic
def create_task(user, space, validated_data):
    assignee_ids = validated_data.pop("assignee_ids", ())
    status = validated_data.pop("status", Task.Status.PENDING)
    task = Task(space=space, created_by=user, **validated_data)
    _apply_status(task, status)
    task.save()
    set_task_assignees(task, assignee_ids)
    return task


@transaction.atomic
def update_task(task, validated_data):
    task = Task.objects.select_for_update().select_related("space").get(pk=task.pk)
    assignee_ids = validated_data.pop("assignee_ids", None)
    status = validated_data.pop("status", None)

    for field, value in validated_data.items():
        setattr(task, field, value)
    if status is not None:
        _apply_status(task, status)
    task.save()

    if assignee_ids is not None:
        set_task_assignees(task, assignee_ids)
    return task
