from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("spaces", "0003_invitation"),
        ("expenses", "0002_expenseparticipant_personal_starting_savings"),
    ]

    operations = [
        migrations.CreateModel(
            name="MonthlyExpenseReport",
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
                (
                    "scope",
                    models.CharField(
                        choices=[("personal", "Personal"), ("common", "Común")],
                        max_length=16,
                    ),
                ),
                ("goal", models.TextField(blank=True)),
                (
                    "monthly_budget",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=12,
                        null=True,
                    ),
                ),
                ("avoidable_category_ids", models.JSONField(blank=True, default=list)),
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
                    "requested_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="requested_expense_reports",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "space",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="monthly_expense_reports",
                        to="spaces.space",
                    ),
                ),
            ],
            options={
                "ordering": ("-month", "-id"),
                "indexes": [
                    models.Index(
                        fields=["space", "month"],
                        name="expense_report_month_idx",
                    ),
                    models.Index(
                        fields=["status", "created_at"],
                        name="expense_report_queue_idx",
                    ),
                ],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("space", "month"),
                        name="unique_monthly_expense_report",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(
                            ("monthly_budget__isnull", True),
                            ("monthly_budget__gte", 0),
                            _connector="OR",
                        ),
                        name="expense_report_nonnegative_budget",
                    ),
                ],
            },
        ),
    ]

