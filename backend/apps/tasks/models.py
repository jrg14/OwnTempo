from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from apps.spaces.models import Membership, Space


class Task(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pendiente"
        COMPLETED = "completed", "Completada"

    class Priority(models.TextChoices):
        LOW = "low", "Baja"
        NORMAL = "normal", "Normal"
        HIGH = "high", "Alta"

    space = models.ForeignKey(
        Space,
        on_delete=models.CASCADE,
        related_name="tasks",
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
    )
    priority = models.CharField(
        max_length=16,
        choices=Priority.choices,
        default=Priority.NORMAL,
    )
    due_date = models.DateField(blank=True, null=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_tasks",
    )
    assignees = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="TaskAssignment",
        related_name="assigned_tasks",
    )
    completed_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at", "-id")
        indexes = [
            models.Index(fields=("space", "status"), name="task_space_status_idx"),
            models.Index(fields=("space", "due_date"), name="task_space_due_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(status="pending", completed_at__isnull=True)
                    | Q(status="completed", completed_at__isnull=False)
                ),
                name="task_completion_matches_status",
            ),
        ]

    def __str__(self):
        return self.title

    def clean(self):
        super().clean()
        self.title = self.title.strip()
        if not self.title:
            raise ValidationError({"title": "El título no puede estar vacío."})

        if self.space_id and self.created_by_id and not Membership.objects.filter(
            space_id=self.space_id,
            user_id=self.created_by_id,
        ).exists():
            raise ValidationError(
                {"created_by": "El creador debe pertenecer al espacio."}
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class TaskAssignment(models.Model):
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name="assignments",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="task_assignments",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("task_id", "id")
        constraints = [
            models.UniqueConstraint(
                fields=("task", "user"),
                name="unique_task_assignment",
            ),
        ]

    def __str__(self):
        return f"{self.user} → {self.task}"

    def clean(self):
        super().clean()
        if self.task_id and self.user_id and not Membership.objects.filter(
            space_id=self.task.space_id,
            user_id=self.user_id,
        ).exists():
            raise ValidationError(
                {"user": "El responsable debe pertenecer al espacio."}
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
