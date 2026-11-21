from rest_framework import serializers

from .models import ShoppingItem, ShoppingList
from .services import (
    ShoppingOperationError,
    create_shopping_item,
    create_shopping_list,
    reorder_shopping_items,
    update_shopping_item,
    update_shopping_list,
)


class ShoppingUserSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(read_only=True)
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)


class ShoppingItemSerializer(serializers.ModelSerializer):
    created_by = ShoppingUserSerializer(read_only=True)

    class Meta:
        model = ShoppingItem
        fields = (
            "id",
            "name",
            "quantity",
            "unit",
            "note",
            "status",
            "position",
            "created_by",
            "purchased_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "position",
            "created_by",
            "purchased_at",
            "created_at",
            "updated_at",
        )

    def validate_name(self, value):
        name = value.strip()
        if not name:
            raise serializers.ValidationError("El producto no puede estar vacío.")
        return name

    def create(self, validated_data):
        return create_shopping_item(
            self.context["request"].user,
            self.context["shopping_list"],
            validated_data,
        )

    def update(self, instance, validated_data):
        return update_shopping_item(instance, validated_data)


class ShoppingListSerializer(serializers.ModelSerializer):
    space_id = serializers.IntegerField(read_only=True)
    created_by = ShoppingUserSerializer(read_only=True)
    pending_count = serializers.SerializerMethodField()
    purchased_count = serializers.SerializerMethodField()
    item_count = serializers.SerializerMethodField()
    items = ShoppingItemSerializer(many=True, read_only=True)

    class Meta:
        model = ShoppingList
        fields = (
            "id",
            "space_id",
            "name",
            "pending_count",
            "purchased_count",
            "item_count",
            "items",
            "created_by",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "space_id",
            "pending_count",
            "purchased_count",
            "item_count",
            "items",
            "created_by",
            "created_at",
            "updated_at",
        )

    def validate_name(self, value):
        name = value.strip()
        if not name:
            raise serializers.ValidationError("El nombre no puede estar vacío.")
        return name

    def _count(self, instance, status=None):
        annotation = "item_count" if status is None else f"{status}_count"
        value = getattr(instance, annotation, None)
        if value is not None:
            return value
        queryset = instance.items.all()
        return queryset.count() if status is None else queryset.filter(status=status).count()

    def get_pending_count(self, instance):
        return self._count(instance, ShoppingItem.Status.PENDING)

    def get_purchased_count(self, instance):
        return self._count(instance, ShoppingItem.Status.PURCHASED)

    def get_item_count(self, instance):
        return self._count(instance)

    def create(self, validated_data):
        return create_shopping_list(
            self.context["request"].user,
            self.context["space"],
            validated_data,
        )

    def update(self, instance, validated_data):
        return update_shopping_list(instance, validated_data)


class ShoppingReorderSerializer(serializers.Serializer):
    item_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        allow_empty=True,
    )

    def save(self, **kwargs):
        try:
            return reorder_shopping_items(
                self.context["shopping_list"],
                self.validated_data["item_ids"],
            )
        except ShoppingOperationError as error:
            raise serializers.ValidationError({"item_ids": [str(error)]}) from error
