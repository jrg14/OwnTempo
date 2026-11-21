from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import WishItem, http_url_validator
from .services import create_wish, update_wish


class WishUserSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(read_only=True)
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)


class WishItemSerializer(serializers.ModelSerializer):
    space_id = serializers.IntegerField(read_only=True)
    created_by = WishUserSerializer(read_only=True)

    class Meta:
        model = WishItem
        fields = (
            "id",
            "space_id",
            "title",
            "description",
            "kind",
            "status",
            "priority",
            "url",
            "image_url",
            "price",
            "currency",
            "created_by",
            "obtained_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "space_id",
            "created_by",
            "obtained_at",
            "created_at",
            "updated_at",
        )

    def validate_title(self, value):
        title = value.strip()
        if not title:
            raise serializers.ValidationError("El título no puede estar vacío.")
        return title

    def validate_currency(self, value):
        currency = value.strip().upper()
        if len(currency) != 3 or not currency.isalpha():
            raise serializers.ValidationError("La moneda debe tener tres letras.")
        return currency

    def _validate_http_url(self, value):
        if not value:
            return value
        try:
            http_url_validator(value)
        except DjangoValidationError as error:
            raise serializers.ValidationError(
                "Introduce una URL HTTP o HTTPS válida."
            ) from error
        return value

    def validate_url(self, value):
        return self._validate_http_url(value)

    def validate_image_url(self, value):
        return self._validate_http_url(value)

    def validate_price(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("El precio no puede ser negativo.")
        return value

    def create(self, validated_data):
        return create_wish(
            self.context["request"].user,
            self.context["space"],
            validated_data,
        )

    def update(self, instance, validated_data):
        return update_wish(instance, validated_data)
