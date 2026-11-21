from rest_framework import serializers

from .models import Task
from .services import TaskOperationError, create_task, update_task


class TaskUserSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(read_only=True)
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)


class TaskSerializer(serializers.ModelSerializer):
    space_id = serializers.IntegerField(read_only=True)
    created_by = TaskUserSerializer(read_only=True)
    assignees = TaskUserSerializer(many=True, read_only=True)
    assignee_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        allow_empty=True,
        required=False,
        write_only=True,
    )

    class Meta:
        model = Task
        fields = (
            "id",
            "space_id",
            "title",
            "description",
            "status",
            "priority",
            "due_date",
            "created_by",
            "assignees",
            "assignee_ids",
            "completed_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "space_id",
            "created_by",
            "assignees",
            "completed_at",
            "created_at",
            "updated_at",
        )
        extra_kwargs = {
            "title": {
                "error_messages": {
                    "blank": "El título no puede estar vacío.",
                },
            },
        }

    def validate_title(self, value):
        title = value.strip()
        if not title:
            raise serializers.ValidationError("El título no puede estar vacío.")
        return title

    def create(self, validated_data):
        try:
            return create_task(
                self.context["request"].user,
                self.context["space"],
                validated_data,
            )
        except TaskOperationError as error:
            raise serializers.ValidationError({"assignee_ids": [str(error)]}) from error

    def update(self, instance, validated_data):
        try:
            return update_task(instance, validated_data)
        except TaskOperationError as error:
            raise serializers.ValidationError({"assignee_ids": [str(error)]}) from error
