from rest_framework import serializers

from .models import CalendarEvent
from .services import create_event, update_event


class CalendarUserSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(read_only=True)
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)


class CalendarEventSerializer(serializers.ModelSerializer):
    space_id = serializers.IntegerField(read_only=True)
    created_by = CalendarUserSerializer(read_only=True)

    class Meta:
        model = CalendarEvent
        fields = (
            "id",
            "space_id",
            "title",
            "description",
            "start_at",
            "end_at",
            "all_day",
            "date",
            "location",
            "color",
            "created_by",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "space_id",
            "created_by",
            "created_at",
            "updated_at",
        )

    def validate_title(self, value):
        title = value.strip()
        if not title:
            raise serializers.ValidationError("El título no puede estar vacío.")
        return title

    def validate(self, attrs):
        instance = self.instance
        all_day = attrs.get("all_day", instance.all_day if instance else False)
        date = attrs.get("date", instance.date if instance else None)
        start_at = attrs.get("start_at", instance.start_at if instance else None)
        end_at = attrs.get("end_at", instance.end_at if instance else None)

        if all_day:
            if not date:
                raise serializers.ValidationError(
                    {"date": "Indica la fecha del evento."}
                )
            if attrs.get("start_at") is not None or attrs.get("end_at") is not None:
                raise serializers.ValidationError(
                    {"all_day": "Un evento de día completo no admite horas."}
                )
        else:
            if start_at is None or end_at is None:
                raise serializers.ValidationError(
                    {"end_at": "Indica el inicio y el final del evento."}
                )
            if end_at <= start_at:
                raise serializers.ValidationError(
                    {"end_at": "El final debe ser posterior al inicio."}
                )
            if attrs.get("date") is not None:
                raise serializers.ValidationError(
                    {"date": "Un evento horario no admite una fecha separada."}
                )
        return attrs

    def create(self, validated_data):
        return create_event(
            self.context["request"].user,
            self.context["space"],
            validated_data,
        )

    def update(self, instance, validated_data):
        return update_event(instance, validated_data)
