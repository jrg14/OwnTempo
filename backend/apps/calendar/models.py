from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q
from django.utils import timezone

from apps.spaces.models import Membership, Space


class CalendarEvent(models.Model):
    class Color(models.TextChoices):
        TEAL = "teal", "Verde"
        AMBER = "amber", "Ámbar"
        ROSE = "rose", "Rosa"
        BLUE = "blue", "Azul"
        VIOLET = "violet", "Violeta"
        SLATE = "slate", "Gris"

    space = models.ForeignKey(
        Space,
        on_delete=models.CASCADE,
        related_name="calendar_events",
    )
    title = models.CharField(max_length=200)
    description = models.TextField(max_length=4000, blank=True)
    start_at = models.DateTimeField(blank=True, null=True)
    end_at = models.DateTimeField(blank=True, null=True)
    all_day = models.BooleanField(default=False)
    date = models.DateField(blank=True, null=True)
    location = models.CharField(max_length=300, blank=True)
    color = models.CharField(
        max_length=16,
        choices=Color.choices,
        default=Color.TEAL,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_calendar_events",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("date", "start_at", "created_at", "id")
        indexes = [
            models.Index(fields=("space", "date"), name="cal_space_date_idx"),
            models.Index(fields=("space", "start_at"), name="cal_space_start_idx"),
            models.Index(fields=("space", "end_at"), name="cal_space_end_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(
                        all_day=True,
                        date__isnull=False,
                        start_at__isnull=True,
                        end_at__isnull=True,
                    )
                    | Q(
                        all_day=False,
                        date__isnull=True,
                        start_at__isnull=False,
                        end_at__isnull=False,
                        end_at__gt=F("start_at"),
                    )
                ),
                name="calendar_event_mode_is_valid",
            ),
        ]

    def __str__(self):
        return self.title

    @property
    def display_date(self):
        if self.all_day:
            return self.date
        return timezone.localtime(self.start_at).date()

    def clean(self):
        super().clean()
        self.title = self.title.strip()
        self.description = self.description.strip()
        self.location = self.location.strip()
        if not self.title:
            raise ValidationError({"title": "El título no puede estar vacío."})
        if self.all_day:
            if not self.date:
                raise ValidationError({"date": "Indica la fecha del evento."})
            if self.start_at is not None or self.end_at is not None:
                raise ValidationError(
                    {"all_day": "Un evento de día completo no admite horas."}
                )
        else:
            if self.date is not None:
                raise ValidationError(
                    {"date": "Un evento horario no admite una fecha separada."}
                )
            if self.start_at is None or self.end_at is None:
                raise ValidationError(
                    {"end_at": "Indica el inicio y el final del evento."}
                )
            if timezone.is_naive(self.start_at) or timezone.is_naive(self.end_at):
                raise ValidationError(
                    {"start_at": "Las fechas deben incluir zona horaria."}
                )
            if self.end_at <= self.start_at:
                raise ValidationError(
                    {"end_at": "El final debe ser posterior al inicio."}
                )
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
