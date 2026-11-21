from datetime import date
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.spaces.models import Space


class PersonalTrainingRecord(models.Model):
    space = models.ForeignKey(Space, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    class Meta:
        abstract = True

    def clean(self):
        super().clean()
        if not self.space_id:
            return
        if self.space.kind != Space.Kind.PERSONAL:
            raise ValidationError({"space": "El entrenamiento solo admite espacios personales."})
        if self.user_id != self.space.created_by_id:
            raise ValidationError({"user": "El usuario debe ser el propietario del espacio personal."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class TrainingProfile(PersonalTrainingRecord):
    height_cm = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(80), MaxValueValidator(250)]
    )
    date_of_birth = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("space", "user"), name="unique_training_profile")
        ]

    def clean(self):
        super().clean()
        if self.date_of_birth and self.date_of_birth >= date.today():
            raise ValidationError({"date_of_birth": "La fecha de nacimiento debe estar en el pasado."})


class StrengthWorkout(PersonalTrainingRecord):
    workout_date = models.DateField()
    started_at = models.TimeField(blank=True, null=True)
    duration_minutes = models.PositiveSmallIntegerField(blank=True, null=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-workout_date", "-started_at", "-id")
        indexes = [models.Index(fields=("space", "user", "workout_date"), name="training_workout_date_idx")]


class StrengthExercise(models.Model):
    workout = models.ForeignKey(StrengthWorkout, on_delete=models.CASCADE, related_name="exercises")
    name = models.CharField(max_length=120)
    order = models.PositiveSmallIntegerField(default=1)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ("order", "id")
        constraints = [models.UniqueConstraint(fields=("workout", "order"), name="unique_exercise_order")]

    def clean(self):
        super().clean()
        self.name = self.name.strip()
        if not self.name:
            raise ValidationError({"name": "El nombre del ejercicio es obligatorio."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class StrengthSet(models.Model):
    exercise = models.ForeignKey(StrengthExercise, on_delete=models.CASCADE, related_name="sets")
    set_number = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    weight_kg = models.DecimalField(
        max_digits=6, decimal_places=2, validators=[MinValueValidator(Decimal("0"))]
    )
    repetitions = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    rest_seconds = models.PositiveSmallIntegerField(blank=True, null=True)

    class Meta:
        ordering = ("set_number", "id")
        constraints = [models.UniqueConstraint(fields=("exercise", "set_number"), name="unique_strength_set_number")]

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class DailySteps(PersonalTrainingRecord):
    date = models.DateField()
    steps = models.PositiveIntegerField()
    goal = models.PositiveIntegerField(blank=True, null=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-date", "-id")
        constraints = [models.UniqueConstraint(fields=("space", "user", "date"), name="unique_daily_steps")]
        indexes = [models.Index(fields=("space", "user", "date"), name="training_steps_date_idx")]


class HealthMeasurement(PersonalTrainingRecord):
    date = models.DateField()
    weight_kg = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("20")), MaxValueValidator(Decimal("500"))],
    )
    bmi = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(Decimal("5")), MaxValueValidator(Decimal("100"))],
    )
    body_fat_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(Decimal("0")), MaxValueValidator(Decimal("100"))],
    )
    subcutaneous_fat_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(Decimal("0")), MaxValueValidator(Decimal("100"))],
    )
    visceral_fat_level = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(Decimal("0")), MaxValueValidator(Decimal("100"))],
    )
    body_water_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(Decimal("0")), MaxValueValidator(Decimal("100"))],
    )
    muscle_mass_kg = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(Decimal("0")), MaxValueValidator(Decimal("300"))],
    )
    bone_mass_kg = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(Decimal("0")), MaxValueValidator(Decimal("30"))],
    )
    basal_metabolic_rate_kcal = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(500), MaxValueValidator(10000)]
    )
    metabolic_age = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(1), MaxValueValidator(150)]
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-date", "-id")
        constraints = [
            models.UniqueConstraint(
                fields=("space", "user", "date"),
                name="unique_health_measurement",
            )
        ]
        indexes = [
            models.Index(
                fields=("space", "user", "date"),
                name="training_health_date_idx",
            )
        ]
