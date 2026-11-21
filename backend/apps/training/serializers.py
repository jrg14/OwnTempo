from rest_framework import serializers
from django.utils import timezone

from .models import DailySteps, HealthMeasurement, StrengthExercise, StrengthSet, StrengthWorkout, TrainingProfile
from .services import create_workout, update_workout


class TrainingProfileSerializer(serializers.ModelSerializer):
    age = serializers.SerializerMethodField()

    class Meta:
        model = TrainingProfile
        fields = ("id", "height_cm", "date_of_birth", "age", "created_at", "updated_at")
        read_only_fields = ("id", "age", "created_at", "updated_at")

    def get_age(self, profile):
        today = timezone.localdate()
        born = profile.date_of_birth
        return today.year - born.year - ((today.month, today.day) < (born.month, born.day))

    def validate_date_of_birth(self, value):
        if value >= timezone.localdate():
            raise serializers.ValidationError("La fecha de nacimiento debe estar en el pasado.")
        return value


class StrengthSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = StrengthSet
        fields = ("id", "set_number", "weight_kg", "repetitions", "rest_seconds")
        read_only_fields = ("id",)


class StrengthExerciseSerializer(serializers.ModelSerializer):
    sets = StrengthSetSerializer(many=True)

    class Meta:
        model = StrengthExercise
        fields = ("id", "name", "order", "notes", "sets")
        read_only_fields = ("id",)

    def validate_sets(self, value):
        if not value:
            raise serializers.ValidationError("Añade al menos una serie.")
        return value


class StrengthWorkoutSerializer(serializers.ModelSerializer):
    exercises = StrengthExerciseSerializer(many=True)
    total_volume_kg = serializers.SerializerMethodField()

    class Meta:
        model = StrengthWorkout
        fields = (
            "id", "workout_date", "started_at", "duration_minutes", "notes",
            "exercises", "total_volume_kg", "created_at", "updated_at",
        )
        read_only_fields = ("id", "total_volume_kg", "created_at", "updated_at")

    def validate_exercises(self, value):
        if not value:
            raise serializers.ValidationError("Añade al menos un ejercicio.")
        return value

    def get_total_volume_kg(self, workout):
        return sum(
            item.weight_kg * item.repetitions
            for exercise in workout.exercises.all()
            for item in exercise.sets.all()
        )

    def create(self, validated_data):
        return create_workout(self.context["request"].user, self.context["space"], validated_data)

    def update(self, instance, validated_data):
        return update_workout(instance, validated_data)


class DailyStepsSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailySteps
        fields = ("id", "date", "steps", "goal", "notes", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")

    def create(self, validated_data):
        return DailySteps.objects.create(
            space=self.context["space"], user=self.context["request"].user, **validated_data
        )

    def validate(self, attrs):
        entry_date = attrs.get("date", getattr(self.instance, "date", None))
        queryset = DailySteps.objects.filter(
            space=self.context["space"],
            user=self.context["request"].user,
            date=entry_date,
        )
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError({"date": "Ya existe un registro de pasos para este día."})
        return attrs


class HealthMeasurementSerializer(serializers.ModelSerializer):
    class Meta:
        model = HealthMeasurement
        fields = (
            "id", "date", "weight_kg", "bmi", "body_fat_percentage",
            "subcutaneous_fat_percentage", "visceral_fat_level",
            "body_water_percentage", "muscle_mass_kg", "bone_mass_kg",
            "basal_metabolic_rate_kcal", "metabolic_age", "notes",
            "created_at", "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def create(self, validated_data):
        return HealthMeasurement.objects.create(
            space=self.context["space"], user=self.context["request"].user, **validated_data
        )

    def validate(self, attrs):
        if self.instance is None:
            required_metrics = (
                "bmi", "body_fat_percentage", "subcutaneous_fat_percentage",
                "visceral_fat_level", "body_water_percentage", "muscle_mass_kg",
                "bone_mass_kg", "basal_metabolic_rate_kcal", "metabolic_age",
            )
            missing = [field for field in required_metrics if attrs.get(field) is None]
            if missing:
                raise serializers.ValidationError(
                    {field: "Este dato de la báscula es obligatorio." for field in missing}
                )
        entry_date = attrs.get("date", getattr(self.instance, "date", None))
        queryset = HealthMeasurement.objects.filter(
            space=self.context["space"],
            user=self.context["request"].user,
            date=entry_date,
        )
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError({"date": "Ya existe una medición de salud para este día."})
        return attrs
