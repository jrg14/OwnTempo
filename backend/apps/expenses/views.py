from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.modules.permissions import HasActiveModule
from apps.spaces.models import Space
from apps.spaces.permissions import IsSpaceMember

from .models import CommonExpense, ExpenseCategory, ExpensePeriod, MonthlyExpenseReport, PersonalExpense
from .monthly_reports import PROMPT_VERSION, normalize_month
from .serializers import CommonExpenseSerializer, ExpenseCategorySerializer, ExpensePeriodSerializer, MonthlyExpenseReportCreateSerializer, MonthlyExpenseReportSerializer, PersonalExpenseSerializer
from .services import ExpenseOperationError, calculate_period_summary, delete_common_expense, delete_personal_expense


def money(value):
    return f"{value:.2f}"


def user_data(user):
    return {"id": user.id, "username": user.username, "first_name": user.first_name, "last_name": user.last_name}


class ExpenseMixin:
    module_key = "expenses"
    permission_classes = (IsAuthenticated, IsSpaceMember, HasActiveModule)

    def get_space(self):
        if not hasattr(self, "_space"):
            self._space = get_object_or_404(Space, pk=self.kwargs["space_id"])
        return self._space

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["space"] = self.get_space()
        return context


class ExpensePeriodListCreateView(ExpenseMixin, ListCreateAPIView):
    serializer_class = ExpensePeriodSerializer

    def get_queryset(self):
        return ExpensePeriod.objects.filter(space_id=self.kwargs["space_id"]).prefetch_related("participants__user")


class ExpensePeriodDetailView(ExpenseMixin, RetrieveUpdateAPIView):
    serializer_class = ExpensePeriodSerializer
    lookup_url_kwarg = "period_id"
    http_method_names = ("get", "patch", "head", "options")

    def get_queryset(self):
        return ExpensePeriod.objects.filter(space_id=self.kwargs["space_id"]).prefetch_related("participants__user")


class PeriodMixin(ExpenseMixin):
    def get_period(self):
        if not hasattr(self, "_period"):
            self._period = get_object_or_404(ExpensePeriod.objects.select_related("space"), pk=self.kwargs["period_id"], space_id=self.kwargs["space_id"])
        return self._period

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["period"] = self.get_period()
        return context


class ExpenseSummaryView(PeriodMixin, APIView):
    def get(self, request, *args, **kwargs):
        try:
            summary = calculate_period_summary(self.get_period())
        except ExpenseOperationError as error:
            return Response({"detail": str(error)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            "total_common": money(summary["total_common"]),
            "categories": [
                {"category_id": row["category_id"], "name": row["category__name"], "color": row["category__color"], "total": money(row["total"])}
                for row in summary["categories"]
            ],
            "participants": [
                {
                    "participant_id": item["participant"].id,
                    "user": user_data(item["participant"].user),
                    "income": money(item["income"]),
                    "expected_contribution": money(item["expected_contribution"]),
                    "paid": money(item["paid"]),
                    "difference": money(item["difference"]),
                    "available_savings": money(item["available_savings"]),
                    "personal_starting_savings": money(item["personal_starting_savings"]),
                    "personal_spent": money(item["personal_spent"]),
                    "final_savings": money(item["final_savings"]),
                }
                for item in summary["participants"]
            ],
            "transfers": [
                {"from": user_data(item["from"].user), "to": user_data(item["to"].user), "amount": money(item["amount"])}
                for item in summary["transfers"]
            ],
        })


class ExpenseCategoryListCreateView(ExpenseMixin, ListCreateAPIView):
    serializer_class = ExpenseCategorySerializer

    def get_queryset(self):
        return ExpenseCategory.objects.filter(space_id=self.kwargs["space_id"])


class ExpenseCategoryDetailView(ExpenseMixin, RetrieveUpdateAPIView):
    serializer_class = ExpenseCategorySerializer
    lookup_url_kwarg = "category_id"
    http_method_names = ("get", "patch", "head", "options")

    def get_queryset(self):
        return ExpenseCategory.objects.filter(space_id=self.kwargs["space_id"])


class CommonExpenseListCreateView(PeriodMixin, ListCreateAPIView):
    serializer_class = CommonExpenseSerializer

    def get_queryset(self):
        if self.get_period().space.kind == Space.Kind.PERSONAL:
            return CommonExpense.objects.none()
        return CommonExpense.objects.filter(period=self.get_period()).select_related("category", "paid_by__user", "created_by")


class CommonExpenseDetailView(PeriodMixin, RetrieveUpdateDestroyAPIView):
    serializer_class = CommonExpenseSerializer
    lookup_url_kwarg = "expense_id"
    http_method_names = ("get", "patch", "delete", "head", "options")

    def get_queryset(self):
        if self.get_period().space.kind == Space.Kind.PERSONAL:
            return CommonExpense.objects.none()
        return CommonExpense.objects.filter(period=self.get_period()).select_related("category", "paid_by__user", "created_by")

    def perform_destroy(self, instance):
        try:
            delete_common_expense(instance)
        except ExpenseOperationError as error:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"detail": str(error)}) from error


class PersonalExpenseListCreateView(PeriodMixin, ListCreateAPIView):
    serializer_class = PersonalExpenseSerializer

    def get_queryset(self):
        return PersonalExpense.objects.filter(period=self.get_period(), owner__user=self.request.user).select_related("category", "owner__user")


class PersonalExpenseDetailView(PeriodMixin, RetrieveUpdateDestroyAPIView):
    serializer_class = PersonalExpenseSerializer
    lookup_url_kwarg = "expense_id"
    http_method_names = ("get", "patch", "delete", "head", "options")

    def get_queryset(self):
        return PersonalExpense.objects.filter(period=self.get_period(), owner__user=self.request.user).select_related("category", "owner__user")

    def perform_destroy(self, instance):
        try:
            delete_personal_expense(instance)
        except ExpenseOperationError as error:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"detail": str(error)}) from error


def _queue_monthly_report(report, validated_data):
    report.goal = validated_data.get("goal", "").strip()
    report.monthly_budget = validated_data.get("monthly_budget")
    report.avoidable_category_ids = validated_data.get("avoidable_category_ids", [])
    report.status = MonthlyExpenseReport.Status.PENDING
    report.input_payload = {}
    report.result_payload = {}
    report.model_name = ""
    report.prompt_version = PROMPT_VERSION
    report.error_message = ""
    report.completed_at = None
    report.save()
    return report


class MonthlyExpenseReportListCreateView(ExpenseMixin, APIView):
    def get(self, request, *args, **kwargs):
        reports = MonthlyExpenseReport.objects.filter(space=self.get_space())
        return Response(MonthlyExpenseReportSerializer(reports, many=True).data)

    def post(self, request, *args, **kwargs):
        serializer = MonthlyExpenseReportCreateSerializer(
            data=request.data,
            context={"space": self.get_space()},
        )
        serializer.is_valid(raise_exception=True)
        month = normalize_month(serializer.validated_data["month"])
        scope = (
            MonthlyExpenseReport.Scope.PERSONAL
            if self.get_space().kind == Space.Kind.PERSONAL
            else MonthlyExpenseReport.Scope.COMMON
        )
        with transaction.atomic():
            report = MonthlyExpenseReport.objects.select_for_update().filter(
                space=self.get_space(), month=month
            ).first()
            if report and report.status == MonthlyExpenseReport.Status.PROCESSING:
                return Response(
                    {"detail": "El informe de este mes ya se está procesando."},
                    status=status.HTTP_409_CONFLICT,
                )
            if report is None:
                report = MonthlyExpenseReport(
                    space=self.get_space(),
                    requested_by=request.user,
                    month=month,
                    scope=scope,
                )
            else:
                report.requested_by = request.user
                report.scope = scope
            _queue_monthly_report(report, serializer.validated_data)
        return Response(
            MonthlyExpenseReportSerializer(report).data,
            status=status.HTTP_202_ACCEPTED,
        )


class MonthlyExpenseReportDetailView(ExpenseMixin, APIView):
    def get_report(self):
        return get_object_or_404(
            MonthlyExpenseReport,
            pk=self.kwargs["report_id"],
            space=self.get_space(),
        )

    def get(self, request, *args, **kwargs):
        return Response(MonthlyExpenseReportSerializer(self.get_report()).data)

    def delete(self, request, *args, **kwargs):
        report = self.get_report()
        if report.status == MonthlyExpenseReport.Status.PROCESSING:
            return Response(
                {"detail": "Espera a que termine la generación antes de eliminar el informe."},
                status=status.HTTP_409_CONFLICT,
            )
        report.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MonthlyExpenseReportRegenerateView(MonthlyExpenseReportDetailView):
    http_method_names = ("post", "head", "options")

    def post(self, request, *args, **kwargs):
        existing = self.get_report()
        serializer = MonthlyExpenseReportCreateSerializer(
            data={
                **request.data,
                "month": existing.month.strftime("%Y-%m"),
            },
            context={"space": self.get_space()},
        )
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            report = MonthlyExpenseReport.objects.select_for_update().get(pk=existing.pk)
            if report.status == MonthlyExpenseReport.Status.PROCESSING:
                return Response(
                    {"detail": "El informe ya se está procesando."},
                    status=status.HTTP_409_CONFLICT,
                )
            report.requested_by = request.user
            _queue_monthly_report(report, serializer.validated_data)
        return Response(
            MonthlyExpenseReportSerializer(report).data,
            status=status.HTTP_202_ACCEPTED,
        )
