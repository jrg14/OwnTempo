import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("spaces", "0003_invitation"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Task",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=200)),
                ("description", models.TextField(blank=True)),
                ("status", models.CharField(choices=[("pending", "Pendiente"), ("completed", "Completada")], default="pending", max_length=16)),
                ("priority", models.CharField(choices=[("low", "Baja"), ("normal", "Normal"), ("high", "Alta")], default="normal", max_length=16)),
                ("due_date", models.DateField(blank=True, null=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="created_tasks", to=settings.AUTH_USER_MODEL)),
                ("space", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="tasks", to="spaces.space")),
            ],
            options={
                "ordering": ("-created_at", "-id"),
                "indexes": [
                    models.Index(fields=["space", "status"], name="task_space_status_idx"),
                    models.Index(fields=["space", "due_date"], name="task_space_due_idx"),
                ],
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(
                            models.Q(("completed_at__isnull", True), ("status", "pending")),
                            models.Q(("completed_at__isnull", False), ("status", "completed")),
                            _connector="OR",
                        ),
                        name="task_completion_matches_status",
                    ),
                ],
            },
        ),
        migrations.CreateModel(
            name="TaskAssignment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("task", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="assignments", to="tasks.task")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="task_assignments", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ("task_id", "id"),
                "constraints": [
                    models.UniqueConstraint(fields=("task", "user"), name="unique_task_assignment"),
                ],
            },
        ),
        migrations.AddField(
            model_name="task",
            name="assignees",
            field=models.ManyToManyField(related_name="assigned_tasks", through="tasks.TaskAssignment", to=settings.AUTH_USER_MODEL),
        ),
    ]
