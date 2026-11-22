from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("spaces", "0003_invitation"),
        ("training", "0002_health_measurements"),
    ]

    operations = [
        migrations.CreateModel(
            name="MonthlyTrainingReport",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "month",
                    models.DateField(help_text="Primer día del mes analizado."),
                ),
                ("goal", models.TextField(blank=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pendiente"),
                            ("processing", "Procesando"),
                            ("completed", "Completado"),
                            ("failed", "Fallido"),
                        ],
                        default="pending",
                        max_length=16,
                    ),
                ),
                ("input_payload", models.JSONField(blank=True, default=dict)),
                ("result_payload", models.JSONField(blank=True, default=dict)),
                ("model_name", models.CharField(blank=True, max_length=120)),
                ("prompt_version", models.CharField(default="1.0", max_length=24)),
                ("error_message", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                (
                    "space",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="spaces.space",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ("-month", "-id"),
                "indexes": [
                    models.Index(
                        fields=["space", "user", "month"],
                        name="training_report_month_idx",
                    ),
                    models.Index(
                        fields=["status", "created_at"],
                        name="training_report_queue_idx",
                    ),
                ],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("space", "user", "month"),
                        name="unique_monthly_training_report",
                    )
                ],
            },
        ),
    ]

