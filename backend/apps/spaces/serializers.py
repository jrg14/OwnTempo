from rest_framework import serializers

from .models import Invitation, Membership, Space
from .services import SpaceOperationError, create_shared_space, invite_user


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


class SharedSpaceCreateSerializer(SpaceSerializer):
    def create(self, validated_data):
        return create_shared_space(
            self.context["request"].user,
            validated_data["name"],
        )


class UserSummarySerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(read_only=True)
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)


class SpaceSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Space
        fields = ("id", "name", "kind")
        read_only_fields = fields


class MembershipSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="user.id", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)
    first_name = serializers.CharField(source="user.first_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name", read_only=True)

    class Meta:
        model = Membership
        fields = ("id", "username", "first_name", "last_name", "role")
        read_only_fields = fields


class InvitationSerializer(serializers.ModelSerializer):
    space = SpaceSummarySerializer(read_only=True)
    invited_user = UserSummarySerializer(read_only=True)
    invited_by = UserSummarySerializer(read_only=True)

    class Meta:
        model = Invitation
        fields = (
            "id",
            "space",
            "invited_user",
            "invited_by",
            "status",
            "created_at",
            "responded_at",
        )
        read_only_fields = fields


class InvitationCreateSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)

    def validate_username(self, value):
        username = value.strip()
        if not username:
            raise serializers.ValidationError("Introduce un nombre de usuario.")
        return username

    def create(self, validated_data):
        try:
            return invite_user(
                self.context["space"],
                self.context["request"].user,
                validated_data["username"],
            )
        except SpaceOperationError as error:
            raise serializers.ValidationError({"detail": str(error)}) from error
