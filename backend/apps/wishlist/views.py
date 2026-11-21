from django.db.models import Case, Count, IntegerField, Value, When
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.modules.permissions import HasActiveModule
from apps.spaces.models import Space
from apps.spaces.permissions import IsSpaceMember

from .models import WishItem
from .serializers import WishItemSerializer


class WishQuerysetMixin:
    module_key = "wishlist"
    permission_classes = (IsAuthenticated, IsSpaceMember, HasActiveModule)
    serializer_class = WishItemSerializer

    def get_space(self):
        if not hasattr(self, "_space"):
            self._space = get_object_or_404(Space, pk=self.kwargs["space_id"])
        return self._space

    def base_queryset(self):
        return WishItem.objects.filter(space_id=self.kwargs["space_id"])

    def get_queryset(self):
        return (
            self.base_queryset()
            .select_related("space", "created_by")
            .annotate(
                status_order=Case(
                    When(status=WishItem.Status.PENDING, then=Value(0)),
                    When(status=WishItem.Status.OBTAINED, then=Value(1)),
                    default=Value(2),
                    output_field=IntegerField(),
                ),
                priority_order=Case(
                    When(priority=WishItem.Priority.HIGH, then=Value(0)),
                    When(priority=WishItem.Priority.NORMAL, then=Value(1)),
                    default=Value(2),
                    output_field=IntegerField(),
                ),
            )
            .order_by("status_order", "priority_order", "-created_at", "-id")
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["space"] = self.get_space()
        return context


class WishListCreateView(WishQuerysetMixin, ListCreateAPIView):
    def get_queryset(self):
        queryset = super().get_queryset()
        status_value = self.request.query_params.get("status")
        if status_value and status_value != "all":
            if status_value not in WishItem.Status.values:
                raise ValidationError({"status": "Estado de deseo no válido."})
            queryset = queryset.filter(status=status_value)

        kind = self.request.query_params.get("kind")
        if kind:
            if kind not in WishItem.Kind.values:
                raise ValidationError({"kind": "Tipo de deseo no válido."})
            queryset = queryset.filter(kind=kind)

        priority = self.request.query_params.get("priority")
        if priority:
            if priority not in WishItem.Priority.values:
                raise ValidationError({"priority": "Prioridad no válida."})
            queryset = queryset.filter(priority=priority)
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        counts = {
            value: self.base_queryset().filter(status=value).count()
            for value in WishItem.Status.values
        }
        counts["total"] = sum(counts.values())
        return Response({"results": serializer.data, "counts": counts})


class WishDetailView(WishQuerysetMixin, RetrieveUpdateDestroyAPIView):
    lookup_url_kwarg = "wish_id"
    http_method_names = ("get", "patch", "delete", "head", "options")
