from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class Space(models.Model):
    class Kind(models.TextChoices):
        PERSONAL = "personal", "Personal"
        SHARED = "shared", "Compartido"

    name = models.CharField(max_length=120)
    kind = models.CharField(max_length=16, choices=Kind.choices)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_spaces",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("kind", "name", "id")
        constraints = [
            models.UniqueConstraint(
                fields=("created_by",),
                condition=Q(kind="personal"),
                name="one_personal_space_per_user",
            ),
        ]

    def __str__(self):
        return self.name


class Membership(models.Model):
    class Role(models.TextChoices):
        OWNER = "owner", "Propietario"
        MEMBER = "member", "Miembro"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="space_memberships",
    )
    space = models.ForeignKey(
        Space,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    role = models.CharField(max_length=16, choices=Role.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("space_id", "id")
        constraints = [
            models.UniqueConstraint(
                fields=("user", "space"),
                name="unique_space_membership",
            ),
        ]

    def __str__(self):
        return f"{self.user} en {self.space}"

    def clean(self):
        super().clean()

        if not self.space_id or self.space.kind != Space.Kind.PERSONAL:
            return

        if self.user_id != self.space.created_by_id:
            raise ValidationError(
                {"user": "Un espacio personal solo admite a su propietario."}
            )

        if self.role != self.Role.OWNER:
            raise ValidationError(
                {"role": "El miembro de un espacio personal debe ser propietario."}
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.space.kind == Space.Kind.PERSONAL:
            raise ValidationError(
                "No se puede eliminar la pertenencia a un espacio personal."
            )

        return super().delete(*args, **kwargs)
