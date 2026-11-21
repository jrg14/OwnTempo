import decimal

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("spaces", "0003_invitation"),
    ]

    operations = [
        migrations.CreateModel(
            name="ExpenseCategory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=80)),
                ("color", models.CharField(default="teal", max_length=16)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("space", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="expense_categories", to="spaces.space")),
            ],
            options={"ordering": ("name", "id")},
        ),
        migrations.CreateModel(
            name="ExpensePeriod",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("year", models.PositiveSmallIntegerField()),
                ("month", models.PositiveSmallIntegerField()),
                ("split_mode", models.CharField(choices=[("equal", "50/50"), ("income", "Proporcional a ingresos"), ("custom", "Porcentajes personalizados")], default="income", max_length=16)),
                ("status", models.CharField(choices=[("open", "Abierto"), ("closed", "Cerrado")], default="open", max_length=16)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="created_expense_periods", to=settings.AUTH_USER_MODEL)),
                ("space", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="expense_periods", to="spaces.space")),
            ],
            options={"ordering": ("-year", "-month", "-id")},
        ),
        migrations.CreateModel(
            name="ExpenseParticipant",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("income", models.DecimalField(decimal_places=2, default=decimal.Decimal("0.00"), max_digits=12)),
                ("custom_percentage", models.DecimalField(decimal_places=2, default=decimal.Decimal("50.00"), max_digits=5)),
                ("position", models.PositiveSmallIntegerField()),
                ("period", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="participants", to="expenses.expenseperiod")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="expense_participations", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ("position", "id")},
        ),
        migrations.CreateModel(
            name="CommonExpense",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("description", models.CharField(max_length=200)),
                ("amount", models.DecimalField(decimal_places=2, max_digits=12)),
                ("spent_on", models.DateField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("category", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="common_expenses", to="expenses.expensecategory")),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="created_common_expenses", to=settings.AUTH_USER_MODEL)),
                ("paid_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="paid_common_expenses", to="expenses.expenseparticipant")),
                ("period", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="common_expenses", to="expenses.expenseperiod")),
            ],
            options={"ordering": ("-spent_on", "-created_at", "-id")},
        ),
        migrations.CreateModel(
            name="PersonalExpense",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("description", models.CharField(max_length=200)),
                ("amount", models.DecimalField(decimal_places=2, max_digits=12)),
                ("spent_on", models.DateField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("category", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="personal_expenses", to="expenses.expensecategory")),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="created_personal_expenses", to=settings.AUTH_USER_MODEL)),
                ("owner", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="personal_expenses", to="expenses.expenseparticipant")),
                ("period", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="personal_expenses", to="expenses.expenseperiod")),
            ],
            options={"ordering": ("-spent_on", "-created_at", "-id")},
        ),
        migrations.AddConstraint(model_name="expensecategory", constraint=models.UniqueConstraint(fields=("space", "name"), name="unique_expense_category_name")),
        migrations.AddConstraint(model_name="expenseperiod", constraint=models.UniqueConstraint(fields=("space", "year", "month"), name="unique_expense_period_month")),
        migrations.AddConstraint(model_name="expenseperiod", constraint=models.CheckConstraint(condition=models.Q(("month__gte", 1), ("month__lte", 12)), name="expense_period_valid_month")),
        migrations.AddConstraint(model_name="expenseperiod", constraint=models.CheckConstraint(condition=models.Q(("year__gte", 2000), ("year__lte", 2200)), name="expense_period_valid_year")),
        migrations.AddConstraint(model_name="expenseparticipant", constraint=models.UniqueConstraint(fields=("period", "user"), name="unique_expense_period_user")),
        migrations.AddConstraint(model_name="expenseparticipant", constraint=models.UniqueConstraint(fields=("period", "position"), name="unique_expense_participant_position")),
        migrations.AddConstraint(model_name="expenseparticipant", constraint=models.CheckConstraint(condition=models.Q(("income__gte", 0)), name="expense_participant_nonnegative_income")),
        migrations.AddConstraint(model_name="expenseparticipant", constraint=models.CheckConstraint(condition=models.Q(("custom_percentage__gte", 0), ("custom_percentage__lte", 100)), name="expense_participant_valid_percentage")),
        migrations.AddConstraint(model_name="commonexpense", constraint=models.CheckConstraint(condition=models.Q(("amount__gt", 0)), name="common_expense_positive_amount")),
        migrations.AddConstraint(model_name="personalexpense", constraint=models.CheckConstraint(condition=models.Q(("amount__gt", 0)), name="personal_expense_positive_amount")),
    ]
