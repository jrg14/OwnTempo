from rest_framework import serializers

from .models import Membership, Space


class SpaceSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()

    class Meta:
        model = Space
        fields = ("id", "name", "kind", "role")
        read_only_fields = ("id", "kind", "role")
        extra_kwargs = {
            "name": {
                "error_messages": {
                    "blank": "El nombre del espacio no puede estar vacío.",
                },
            },
        }

    def get_role(self, space):
        membership = self.context.get("membership")
        if membership is not None and membership.space_id == space.id:
            return membership.role

        user = self.context["request"].user
        return Membership.objects.only("role").get(user=user, space=space).role

    def validate_name(self, value):
        name = value.strip()
        if not name:
            raise serializers.ValidationError(
                "El nombre del espacio no puede estar vacío."
            )
        return name
