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


class Invitation(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pendiente"
        ACCEPTED = "accepted", "Aceptada"
        REJECTED = "rejected", "Rechazada"
        CANCELLED = "cancelled", "Cancelada"

    space = models.ForeignKey(
        Space,
        on_delete=models.CASCADE,
        related_name="invitations",
    )
    invited_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="space_invitations",
    )
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_space_invitations",
    )
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ("-created_at", "-id")
        constraints = [
            models.UniqueConstraint(
                fields=("space", "invited_user"),
                condition=Q(status="pending"),
                name="unique_pending_space_invitation",
            ),
        ]

    def __str__(self):
        return f"Invitación de {self.invited_user} a {self.space}"

    def clean(self):
        super().clean()

        if not self.space_id or self.space.kind != Space.Kind.SHARED:
            raise ValidationError(
                {"space": "Solo los espacios compartidos admiten invitaciones."}
            )

        if self.status != self.Status.PENDING:
            return

        if Membership.objects.filter(
            space_id=self.space_id,
            user_id=self.invited_user_id,
        ).exists():
            raise ValidationError(
                {"invited_user": "El usuario ya pertenece a este espacio."}
            )

        if not Membership.objects.filter(
            space_id=self.space_id,
            user_id=self.invited_by_id,
            role=Membership.Role.OWNER,
        ).exists():
            raise ValidationError(
                {"invited_by": "Solo el propietario puede invitar miembros."}
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
