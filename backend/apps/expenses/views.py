from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.modules.permissions import HasActiveModule
from apps.spaces.models import Space
from apps.spaces.permissions import IsSpaceMember

from .models import CommonExpense, ExpenseCategory, ExpensePeriod, PersonalExpense
from .serializers import CommonExpenseSerializer, ExpenseCategorySerializer, ExpensePeriodSerializer, PersonalExpenseSerializer
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
