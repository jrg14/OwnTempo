from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from apps.spaces.models import Membership, Space


class ExpenseCategory(models.Model):
    space = models.ForeignKey(Space, on_delete=models.CASCADE, related_name="expense_categories")
    name = models.CharField(max_length=80)
    color = models.CharField(max_length=16, default="teal")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name", "id")
        constraints = [
            models.UniqueConstraint(fields=("space", "name"), name="unique_expense_category_name"),
        ]

    def clean(self):
        super().clean()
        self.name = self.name.strip()
        if not self.name:
            raise ValidationError({"name": "El nombre no puede estar vacío."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class ExpensePeriod(models.Model):
    class SplitMode(models.TextChoices):
        EQUAL = "equal", "50/50"
        INCOME = "income", "Proporcional a ingresos"
        CUSTOM = "custom", "Porcentajes personalizados"

    class Status(models.TextChoices):
        OPEN = "open", "Abierto"
        CLOSED = "closed", "Cerrado"

    space = models.ForeignKey(Space, on_delete=models.CASCADE, related_name="expense_periods")
    year = models.PositiveSmallIntegerField()
    month = models.PositiveSmallIntegerField()
    split_mode = models.CharField(max_length=16, choices=SplitMode.choices, default=SplitMode.INCOME)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.OPEN)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_expense_periods")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-year", "-month", "-id")
        constraints = [
            models.UniqueConstraint(fields=("space", "year", "month"), name="unique_expense_period_month"),
            models.CheckConstraint(condition=Q(month__gte=1, month__lte=12), name="expense_period_valid_month"),
            models.CheckConstraint(condition=Q(year__gte=2000, year__lte=2200), name="expense_period_valid_year"),
        ]

    def clean(self):
        super().clean()
        if self.space_id and self.created_by_id and not Membership.objects.filter(space_id=self.space_id, user_id=self.created_by_id).exists():
            raise ValidationError({"created_by": "El creador debe pertenecer al espacio."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class ExpenseParticipant(models.Model):
    period = models.ForeignKey(ExpensePeriod, on_delete=models.CASCADE, related_name="participants")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="expense_participations")
    income = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    personal_starting_savings = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    custom_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("50.00"))
    position = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ("position", "id")
        constraints = [
            models.UniqueConstraint(fields=("period", "user"), name="unique_expense_period_user"),
            models.UniqueConstraint(fields=("period", "position"), name="unique_expense_participant_position"),
            models.CheckConstraint(condition=Q(income__gte=0), name="expense_participant_nonnegative_income"),
            models.CheckConstraint(condition=Q(personal_starting_savings__gte=0), name="expense_participant_nonnegative_personal_savings"),
            models.CheckConstraint(condition=Q(custom_percentage__gte=0, custom_percentage__lte=100), name="expense_participant_valid_percentage"),
        ]

    def clean(self):
        super().clean()
        if self.period_id and self.user_id and not Membership.objects.filter(space_id=self.period.space_id, user_id=self.user_id).exists():
            raise ValidationError({"user": "La persona debe pertenecer al espacio."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class CommonExpense(models.Model):
    period = models.ForeignKey(ExpensePeriod, on_delete=models.CASCADE, related_name="common_expenses")
    category = models.ForeignKey(ExpenseCategory, on_delete=models.PROTECT, related_name="common_expenses")
    description = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    spent_on = models.DateField()
    paid_by = models.ForeignKey(ExpenseParticipant, on_delete=models.PROTECT, related_name="paid_common_expenses")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_common_expenses")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-spent_on", "-created_at", "-id")
        constraints = [models.CheckConstraint(condition=Q(amount__gt=0), name="common_expense_positive_amount")]

    def clean(self):
        super().clean()
        self.description = self.description.strip()
        if not self.description:
            raise ValidationError({"description": "La descripción no puede estar vacía."})
        if self.period_id and self.category_id and self.category.space_id != self.period.space_id:
            raise ValidationError({"category": "La categoría no pertenece al espacio."})
        if self.period_id and self.paid_by_id and self.paid_by.period_id != self.period_id:
            raise ValidationError({"paid_by": "La persona no pertenece al periodo."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class PersonalExpense(models.Model):
    period = models.ForeignKey(ExpensePeriod, on_delete=models.CASCADE, related_name="personal_expenses")
    owner = models.ForeignKey(ExpenseParticipant, on_delete=models.PROTECT, related_name="personal_expenses")
    category = models.ForeignKey(ExpenseCategory, on_delete=models.PROTECT, related_name="personal_expenses")
    description = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    spent_on = models.DateField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_personal_expenses")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-spent_on", "-created_at", "-id")
        constraints = [models.CheckConstraint(condition=Q(amount__gt=0), name="personal_expense_positive_amount")]

    def clean(self):
        super().clean()
        self.description = self.description.strip()
        if not self.description:
            raise ValidationError({"description": "La descripción no puede estar vacía."})
        if self.period_id and self.category_id and self.category.space_id != self.period.space_id:
            raise ValidationError({"category": "La categoría no pertenece al espacio."})
        if self.period_id and self.owner_id and self.owner.period_id != self.period_id:
            raise ValidationError({"owner": "La persona no pertenece al periodo."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
