from datetime import timedelta

from django.db import transaction
from django.db.models import Avg, Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, UpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView

from apps.modules.permissions import HasActiveModule
from apps.spaces.models import Space
from apps.spaces.permissions import IsSpaceMember

from .models import DailySteps, HealthMeasurement, MonthlyTrainingReport, StrengthWorkout, TrainingProfile
from .monthly_reports import PROMPT_VERSION, normalize_month
from .permissions import IsPersonalTrainingSpace
from .serializers import (
    DailyStepsSerializer,
    HealthMeasurementSerializer,
    MonthlyTrainingReportCreateSerializer,
    MonthlyTrainingReportSerializer,
    StrengthWorkoutSerializer,
    TrainingProfileSerializer,
)


class TrainingMixin:
    module_key = "training"
    permission_classes = (IsAuthenticated, IsSpaceMember, HasActiveModule, IsPersonalTrainingSpace)

    def get_space(self):
        if not hasattr(self, "_space"):
            self._space = get_object_or_404(
                Space,
                pk=self.kwargs["space_id"],
                kind=Space.Kind.PERSONAL,
                created_by=self.request.user,
            )
        return self._space

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["space"] = self.get_space()
        return context


def filter_by_dates(queryset, request):
    for parameter, lookup in (("from", "date__gte"), ("to", "date__lte")):
        value = request.query_params.get(parameter)
        if not value:
            continue
        parsed = parse_date(value)
        if parsed is None:
            raise ValidationError({parameter: "La fecha debe usar el formato AAAA-MM-DD."})
        queryset = queryset.filter(**{lookup: parsed})
    return queryset


class TrainingProfileView(TrainingMixin, APIView):
    def get(self, request, *args, **kwargs):
        profile = get_object_or_404(
            TrainingProfile,
            space=self.get_space(),
            user=request.user,
        )
        return Response(TrainingProfileSerializer(profile).data)

    def put(self, request, *args, **kwargs):
        profile = TrainingProfile.objects.filter(
            space=self.get_space(), user=request.user
        ).first()
        serializer = TrainingProfileSerializer(profile, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(space=self.get_space(), user=request.user)
        return Response(serializer.data, status=200 if profile else 201)


class WorkoutListCreateView(TrainingMixin, ListCreateAPIView):
    serializer_class = StrengthWorkoutSerializer

    def get_queryset(self):
        queryset = (
            StrengthWorkout.objects.filter(
                space_id=self.kwargs["space_id"], user=self.request.user
            )
            .prefetch_related("exercises__sets")
        )
        from_value = self.request.query_params.get("from")
        to_value = self.request.query_params.get("to")
        for parameter, value, lookup in (
            ("from", from_value, "workout_date__gte"),
            ("to", to_value, "workout_date__lte"),
        ):
            if value:
                parsed = parse_date(value)
                if parsed is None:
                    raise ValidationError({parameter: "La fecha debe usar el formato AAAA-MM-DD."})
                queryset = queryset.filter(**{lookup: parsed})
        return queryset


class WorkoutDetailView(TrainingMixin, RetrieveUpdateDestroyAPIView):
    serializer_class = StrengthWorkoutSerializer
    lookup_url_kwarg = "workout_id"
    http_method_names = ("get", "patch", "delete", "head", "options")

    def get_queryset(self):
        return StrengthWorkout.objects.filter(
            space_id=self.kwargs["space_id"], user=self.request.user
        ).prefetch_related("exercises__sets")


class StepsListCreateView(TrainingMixin, ListCreateAPIView):
    serializer_class = DailyStepsSerializer

    def get_queryset(self):
        queryset = DailySteps.objects.filter(
            space_id=self.kwargs["space_id"], user=self.request.user
        )
        return filter_by_dates(queryset, self.request)


class StepsDetailView(TrainingMixin, UpdateAPIView):
    serializer_class = DailyStepsSerializer
    lookup_url_kwarg = "steps_id"
    http_method_names = ("patch", "head", "options")

    def get_queryset(self):
        return DailySteps.objects.filter(
            space_id=self.kwargs["space_id"], user=self.request.user
        )


class HealthListCreateView(TrainingMixin, ListCreateAPIView):
    serializer_class = HealthMeasurementSerializer

    def get_queryset(self):
        queryset = HealthMeasurement.objects.filter(
            space_id=self.kwargs["space_id"], user=self.request.user
        )
        return filter_by_dates(queryset, self.request)


class HealthDetailView(TrainingMixin, RetrieveUpdateDestroyAPIView):
    serializer_class = HealthMeasurementSerializer
    lookup_url_kwarg = "measurement_id"
    http_method_names = ("get", "patch", "delete", "head", "options")

    def get_queryset(self):
        return HealthMeasurement.objects.filter(
            space_id=self.kwargs["space_id"], user=self.request.user
        )


class TrainingSummaryView(TrainingMixin, APIView):
    def get(self, request, *args, **kwargs):
        today = timezone.localdate()
        week_start = today - timedelta(days=6)
        history_start = today - timedelta(days=29)
        steps = DailySteps.objects.filter(
            space=self.get_space(), user=request.user, date__gte=history_start, date__lte=today
        )
        health_measurements = HealthMeasurement.objects.filter(
            space=self.get_space(), user=request.user
        ).order_by("date", "id")
        workouts = StrengthWorkout.objects.filter(
            space=self.get_space(), user=request.user
        )
        week_steps = steps.filter(date__gte=week_start)
        aggregates = week_steps.aggregate(total=Sum("steps"), average=Avg("steps"))
        latest_measurement = health_measurements.last()
        first_measurement = health_measurements.first()
        previous_measurement = (
            health_measurements.exclude(pk=latest_measurement.pk).last()
            if latest_measurement else None
        )

        return Response(
            {
                "today": {
                    "steps": steps.filter(date=today).values_list("steps", flat=True).first(),
                    "steps_goal": steps.filter(date=today).values_list("goal", flat=True).first(),
                    "workout_count": workouts.filter(workout_date=today).count(),
                    "weight_kg": latest_measurement.weight_kg if latest_measurement and latest_measurement.date == today else None,
                },
                "week": {
                    "total_steps": aggregates["total"] or 0,
                    "average_steps": round(aggregates["average"] or 0),
                    "workout_count": workouts.filter(workout_date__gte=week_start, workout_date__lte=today).count(),
                },
                "health": {
                    "latest": (
                        HealthMeasurementSerializer(latest_measurement).data
                        if latest_measurement else None
                    ),
                    "weight_change_from_first_kg": (
                        latest_measurement.weight_kg - first_measurement.weight_kg
                        if latest_measurement and first_measurement else None
                    ),
                    "weight_change_from_previous_kg": (
                        latest_measurement.weight_kg - previous_measurement.weight_kg
                        if latest_measurement and previous_measurement else None
                    ),
                },
                "steps_history": list(steps.order_by("date").values("date", "steps", "goal")),
                "health_history": HealthMeasurementSerializer(
                    health_measurements.filter(date__gte=history_start), many=True
                ).data,
            }
        )


def _queue_report(report, goal=None):
    if goal is not None:
        report.goal = goal.strip()
    report.status = MonthlyTrainingReport.Status.PENDING
    report.input_payload = {}
    report.result_payload = {}
    report.model_name = ""
    report.prompt_version = PROMPT_VERSION
    report.error_message = ""
    report.completed_at = None
    report.save()
    return report


class MonthlyReportListCreateView(TrainingMixin, APIView):
    def get(self, request, *args, **kwargs):
        reports = MonthlyTrainingReport.objects.filter(
            space=self.get_space(), user=request.user
        )
        return Response(MonthlyTrainingReportSerializer(reports, many=True).data)

    def post(self, request, *args, **kwargs):
        serializer = MonthlyTrainingReportCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        month = normalize_month(serializer.validated_data["month"])
        goal = serializer.validated_data.get("goal", "")

        with transaction.atomic():
            report = MonthlyTrainingReport.objects.select_for_update().filter(
                space=self.get_space(), user=request.user, month=month
            ).first()
            if report and report.status == MonthlyTrainingReport.Status.PROCESSING:
                return Response(
                    {"detail": "El informe de este mes ya se está procesando."},
                    status=status.HTTP_409_CONFLICT,
                )
            if report is None:
                report = MonthlyTrainingReport(
                    space=self.get_space(),
                    user=request.user,
                    month=month,
                    goal=goal.strip(),
                    prompt_version=PROMPT_VERSION,
                )
            _queue_report(report, goal)

        return Response(
            MonthlyTrainingReportSerializer(report).data,
            status=status.HTTP_202_ACCEPTED,
        )


class MonthlyReportDetailView(TrainingMixin, APIView):
    def get_report(self):
        return get_object_or_404(
            MonthlyTrainingReport,
            pk=self.kwargs["report_id"],
            space=self.get_space(),
            user=self.request.user,
        )

    def get(self, request, *args, **kwargs):
        return Response(MonthlyTrainingReportSerializer(self.get_report()).data)

    def delete(self, request, *args, **kwargs):
        report = self.get_report()
        if report.status == MonthlyTrainingReport.Status.PROCESSING:
            return Response(
                {"detail": "Espera a que termine la generación antes de eliminar el informe."},
                status=status.HTTP_409_CONFLICT,
            )
        report.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MonthlyReportRegenerateView(MonthlyReportDetailView):
    http_method_names = ("post", "head", "options")

    def post(self, request, *args, **kwargs):
        goal = request.data.get("goal")
        if goal is not None and not isinstance(goal, str):
            raise ValidationError({"goal": "El objetivo debe ser texto."})
        if isinstance(goal, str) and len(goal) > 1000:
            raise ValidationError({"goal": "El objetivo no puede superar 1000 caracteres."})

        with transaction.atomic():
            report = MonthlyTrainingReport.objects.select_for_update().get(
                pk=self.get_report().pk
            )
            if report.status == MonthlyTrainingReport.Status.PROCESSING:
                return Response(
                    {"detail": "El informe ya se está procesando."},
                    status=status.HTTP_409_CONFLICT,
                )
            _queue_report(report, goal)
        return Response(
            MonthlyTrainingReportSerializer(report).data,
            status=status.HTTP_202_ACCEPTED,
        )
