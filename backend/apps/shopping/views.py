from django.db.models import Count, Prefetch, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import (
    CreateAPIView,
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.modules.permissions import HasActiveModule
from apps.spaces.models import Space
from apps.spaces.permissions import IsSpaceMember

from .models import ShoppingItem, ShoppingList
from .serializers import (
    ShoppingItemSerializer,
    ShoppingListSerializer,
    ShoppingReorderSerializer,
)


def shopping_lists_for_space(space_id):
    return (
        ShoppingList.objects.filter(space_id=space_id)
        .select_related("space", "created_by")
        .annotate(
            pending_count=Count(
                "items",
                filter=Q(items__status=ShoppingItem.Status.PENDING),
            ),
            purchased_count=Count(
                "items",
                filter=Q(items__status=ShoppingItem.Status.PURCHASED),
            ),
            item_count=Count("items"),
        )
        .order_by("-updated_at", "-id")
    )


class ShoppingPermissionMixin:
    module_key = "shopping"
    permission_classes = (IsAuthenticated, IsSpaceMember, HasActiveModule)

    def get_space(self):
        if not hasattr(self, "_space"):
            self._space = get_object_or_404(Space, pk=self.kwargs["space_id"])
        return self._space

    def get_shopping_list(self):
        if not hasattr(self, "_shopping_list"):
            self._shopping_list = get_object_or_404(
                shopping_lists_for_space(self.kwargs["space_id"]),
                pk=self.kwargs["list_id"],
            )
        return self._shopping_list

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["space"] = self.get_space()
        if "list_id" in self.kwargs:
            context["shopping_list"] = self.get_shopping_list()
        return context


class ShoppingListListCreateView(ShoppingPermissionMixin, ListCreateAPIView):
    serializer_class = ShoppingListSerializer

    def get_queryset(self):
        return shopping_lists_for_space(self.kwargs["space_id"])


class ShoppingListDetailView(
    ShoppingPermissionMixin,
    RetrieveUpdateDestroyAPIView,
):
    serializer_class = ShoppingListSerializer
    lookup_url_kwarg = "list_id"
    http_method_names = ("get", "patch", "delete", "head", "options")

    def get_queryset(self):
        items = ShoppingItem.objects.select_related("created_by").order_by(
            "status", "position", "id"
        )
        status_value = self.request.query_params.get("status")
        if status_value and status_value != "all":
            if status_value not in ShoppingItem.Status.values:
                raise ValidationError({"status": "Estado de producto no válido."})
            items = items.filter(status=status_value)
        return shopping_lists_for_space(self.kwargs["space_id"]).prefetch_related(
            Prefetch("items", queryset=items)
        )


class ShoppingItemCreateView(ShoppingPermissionMixin, CreateAPIView):
    serializer_class = ShoppingItemSerializer


class ShoppingItemDetailView(
    ShoppingPermissionMixin,
    RetrieveUpdateDestroyAPIView,
):
    serializer_class = ShoppingItemSerializer
    lookup_url_kwarg = "item_id"
    http_method_names = ("patch", "delete", "head", "options")

    def get_queryset(self):
        return ShoppingItem.objects.filter(
            shopping_list_id=self.kwargs["list_id"],
            shopping_list__space_id=self.kwargs["space_id"],
        ).select_related("shopping_list", "created_by")

    def perform_destroy(self, instance):
        shopping_list_id = instance.shopping_list_id
        super().perform_destroy(instance)
        ShoppingList.objects.filter(pk=shopping_list_id).update(
            updated_at=timezone.now()
        )


class ShoppingItemReorderView(ShoppingPermissionMixin, APIView):
    def post(self, request, *args, **kwargs):
        serializer = ShoppingReorderSerializer(
            data=request.data,
            context={"shopping_list": self.get_shopping_list()},
        )
        serializer.is_valid(raise_exception=True)
        items = serializer.save()
        return Response(
            ShoppingItemSerializer(items, many=True).data,
            status=status.HTTP_200_OK,
        )
