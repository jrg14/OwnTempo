from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db import models
from django.db.models import Q

from apps.spaces.models import Membership, Space


http_url_validator = URLValidator(schemes=("http", "https"))


class WishItem(models.Model):
    class Kind(models.TextChoices):
        PRODUCT = "product", "Producto"
        EXPERIENCE = "experience", "Experiencia"
        IDEA = "idea", "Idea"

    class Status(models.TextChoices):
        PENDING = "pending", "Pendiente"
        OBTAINED = "obtained", "Conseguido"
        DISMISSED = "dismissed", "Descartado"

    class Priority(models.TextChoices):
        LOW = "low", "Baja"
        NORMAL = "normal", "Normal"
        HIGH = "high", "Alta"

    space = models.ForeignKey(
        Space,
        on_delete=models.CASCADE,
        related_name="wish_items",
    )
    title = models.CharField(max_length=200)
    description = models.TextField(max_length=2000, blank=True)
    kind = models.CharField(
        max_length=16,
        choices=Kind.choices,
        default=Kind.PRODUCT,
    )
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
    url = models.URLField(max_length=500, blank=True, validators=(http_url_validator,))
    image_url = models.URLField(
        max_length=500,
        blank=True,
        validators=(http_url_validator,),
    )
    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
    )
    currency = models.CharField(max_length=3, default="EUR")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_wish_items",
    )
    obtained_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at", "-id")
        indexes = [
            models.Index(fields=("space", "status"), name="wish_space_status_idx"),
            models.Index(fields=("space", "kind"), name="wish_space_kind_idx"),
            models.Index(fields=("space", "priority"), name="wish_space_priority_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(price__isnull=True) | Q(price__gte=0),
                name="wish_price_non_negative",
            ),
            models.CheckConstraint(
                condition=(
                    Q(status="obtained", obtained_at__isnull=False)
                    | ~Q(status="obtained") & Q(obtained_at__isnull=True)
                ),
                name="wish_obtained_at_matches_status",
            ),
        ]

    def __str__(self):
        return self.title

    def clean(self):
        super().clean()
        self.title = self.title.strip()
        self.description = self.description.strip()
        self.currency = self.currency.strip().upper()
        if not self.title:
            raise ValidationError({"title": "El título no puede estar vacío."})
        if len(self.currency) != 3 or not self.currency.isalpha():
            raise ValidationError(
                {"currency": "La moneda debe tener tres letras."}
            )
        if self.price is not None and self.price < 0:
            raise ValidationError({"price": "El precio no puede ser negativo."})
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
