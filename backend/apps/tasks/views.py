from django.db.models import Case, IntegerField, Value, When
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated

from apps.modules.permissions import HasActiveModule
from apps.spaces.models import Space
from apps.spaces.permissions import IsSpaceMember

from .models import Task
from .serializers import TaskSerializer


class TaskQuerysetMixin:
    module_key = "tasks"
    permission_classes = (IsAuthenticated, IsSpaceMember, HasActiveModule)
    serializer_class = TaskSerializer

    def get_space(self):
        if not hasattr(self, "_space"):
            self._space = get_object_or_404(Space, pk=self.kwargs["space_id"])
        return self._space

    def get_queryset(self):
        return (
            Task.objects.filter(space_id=self.kwargs["space_id"])
            .select_related("space", "created_by")
            .prefetch_related("assignees")
            .annotate(
                status_order=Case(
                    When(status=Task.Status.PENDING, then=Value(0)),
                    default=Value(1),
                    output_field=IntegerField(),
                ),
                due_order=Case(
                    When(due_date__isnull=True, then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField(),
                ),
            )
            .order_by("status_order", "due_order", "due_date", "-created_at")
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["space"] = self.get_space()
        return context


class TaskListCreateView(TaskQuerysetMixin, ListCreateAPIView):
    def get_queryset(self):
        queryset = super().get_queryset()
        status_value = self.request.query_params.get("status")
        if status_value:
            if status_value not in Task.Status.values:
                raise ValidationError({"status": "Estado de tarea no válido."})
            queryset = queryset.filter(status=status_value)

        assigned_to = self.request.query_params.get("assigned_to")
        if assigned_to:
            try:
                assigned_to_id = int(assigned_to)
            except ValueError as error:
                raise ValidationError(
                    {"assigned_to": "El responsable no es válido."}
                ) from error
            queryset = queryset.filter(assignments__user_id=assigned_to_id)

        due = self.request.query_params.get("due")
        today = timezone.localdate()
        if due == "overdue":
            queryset = queryset.filter(
                status=Task.Status.PENDING,
                due_date__lt=today,
            )
        elif due == "today":
            queryset = queryset.filter(due_date=today)
        elif due == "upcoming":
            queryset = queryset.filter(due_date__gt=today)
        elif due == "none":
            queryset = queryset.filter(due_date__isnull=True)
        elif due:
            raise ValidationError({"due": "Filtro de vencimiento no válido."})

        return queryset.distinct()


class TaskDetailView(TaskQuerysetMixin, RetrieveUpdateDestroyAPIView):
    lookup_url_kwarg = "task_id"
    http_method_names = ("get", "patch", "delete", "head", "options")
