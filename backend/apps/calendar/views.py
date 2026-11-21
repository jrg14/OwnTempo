from datetime import date, datetime, time, timedelta

from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated

from apps.modules.permissions import HasActiveModule
from apps.spaces.models import Space
from apps.spaces.permissions import IsSpaceMember

from .models import CalendarEvent
from .serializers import CalendarEventSerializer


def parse_range(query_params):
    raw_from = query_params.get("from")
    raw_to = query_params.get("to")
    if not raw_from or not raw_to:
        raise ValidationError(
            {"range": "Indica los parámetros from y to en formato AAAA-MM-DD."}
        )
    try:
        start = date.fromisoformat(raw_from)
        end = date.fromisoformat(raw_to)
    except ValueError as error:
        raise ValidationError({"range": "El rango de fechas no es válido."}) from error
    if start > end:
        raise ValidationError({"range": "La fecha inicial debe ser anterior al final."})
    if (end - start).days >= 93:
        raise ValidationError({"range": "El rango no puede superar 93 días."})
    return start, end


class CalendarEventQuerysetMixin:
    module_key = "calendar"
    permission_classes = (IsAuthenticated, IsSpaceMember, HasActiveModule)
    serializer_class = CalendarEventSerializer

    def get_space(self):
        if not hasattr(self, "_space"):
            self._space = get_object_or_404(Space, pk=self.kwargs["space_id"])
        return self._space

    def get_queryset(self):
        return CalendarEvent.objects.filter(
            space_id=self.kwargs["space_id"]
        ).select_related("space", "created_by")

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["space"] = self.get_space()
        return context


class CalendarEventListCreateView(
    CalendarEventQuerysetMixin,
    ListCreateAPIView,
):
    def get_queryset(self):
        queryset = super().get_queryset()
        start, end = parse_range(self.request.query_params)
        current_timezone = timezone.get_current_timezone()
        start_at = timezone.make_aware(datetime.combine(start, time.min), current_timezone)
        end_at = timezone.make_aware(
            datetime.combine(end + timedelta(days=1), time.min),
            current_timezone,
        )
        return queryset.filter(
            Q(all_day=True, date__range=(start, end))
            | Q(all_day=False, start_at__lt=end_at, end_at__gt=start_at)
        ).order_by("date", "start_at", "created_at", "id")


class CalendarEventDetailView(
    CalendarEventQuerysetMixin,
    RetrieveUpdateDestroyAPIView,
):
    lookup_url_kwarg = "event_id"
    http_method_names = ("get", "patch", "delete", "head", "options")
