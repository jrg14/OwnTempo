from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from apps.spaces.models import Membership, Space


class ShoppingList(models.Model):
    space = models.ForeignKey(
        Space,
        on_delete=models.CASCADE,
        related_name="shopping_lists",
    )
    name = models.CharField(max_length=120)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_shopping_lists",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-updated_at", "-id")
        indexes = [
            models.Index(fields=("space", "updated_at"), name="shop_list_space_updated_idx"),
        ]

    def __str__(self):
        return self.name

    def clean(self):
        super().clean()
        self.name = self.name.strip()
        if not self.name:
            raise ValidationError({"name": "El nombre no puede estar vacío."})
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


class ShoppingItem(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pendiente"
        PURCHASED = "purchased", "Comprado"

    shopping_list = models.ForeignKey(
        ShoppingList,
        on_delete=models.CASCADE,
        related_name="items",
    )
    name = models.CharField(max_length=200)
    quantity = models.CharField(max_length=80, blank=True)
    unit = models.CharField(max_length=80, blank=True)
    note = models.CharField(max_length=500, blank=True)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
    )
    position = models.PositiveIntegerField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_shopping_items",
    )
    purchased_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("status", "position", "id")
        indexes = [
            models.Index(
                fields=("shopping_list", "status", "position"),
                name="shop_item_list_status_pos_idx",
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=("shopping_list", "position"),
                name="unique_shopping_item_position",
            ),
            models.CheckConstraint(
                condition=(
                    Q(status="pending", purchased_at__isnull=True)
                    | Q(status="purchased", purchased_at__isnull=False)
                ),
                name="shopping_item_purchase_matches_status",
            ),
        ]

    def __str__(self):
        return self.name

    @property
    def space_id(self):
        return self.shopping_list.space_id

    def clean(self):
        super().clean()
        self.name = self.name.strip()
        self.quantity = self.quantity.strip()
        self.unit = self.unit.strip()
        self.note = self.note.strip()
        if not self.name:
            raise ValidationError({"name": "El producto no puede estar vacío."})
        if (
            self.shopping_list_id
            and self.created_by_id
            and not Membership.objects.filter(
                space_id=self.shopping_list.space_id,
                user_id=self.created_by_id,
            ).exists()
        ):
            raise ValidationError(
                {"created_by": "El creador debe pertenecer al espacio."}
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
