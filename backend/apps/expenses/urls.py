from django.urls import path

from .views import (
    CommonExpenseDetailView,
    CommonExpenseListCreateView,
    ExpenseCategoryDetailView,
    ExpenseCategoryListCreateView,
    ExpensePeriodDetailView,
    ExpensePeriodListCreateView,
    ExpenseSummaryView,
    PersonalExpenseDetailView,
    PersonalExpenseListCreateView,
    MonthlyExpenseReportDetailView,
    MonthlyExpenseReportListCreateView,
    MonthlyExpenseReportRegenerateView,
)

app_name = "expenses"

urlpatterns = [
    path("spaces/<int:space_id>/expenses/periods/", ExpensePeriodListCreateView.as_view(), name="period-list"),
    path("spaces/<int:space_id>/expenses/periods/<int:period_id>/", ExpensePeriodDetailView.as_view(), name="period-detail"),
    path("spaces/<int:space_id>/expenses/periods/<int:period_id>/summary/", ExpenseSummaryView.as_view(), name="summary"),
    path("spaces/<int:space_id>/expenses/categories/", ExpenseCategoryListCreateView.as_view(), name="category-list"),
    path("spaces/<int:space_id>/expenses/categories/<int:category_id>/", ExpenseCategoryDetailView.as_view(), name="category-detail"),
    path("spaces/<int:space_id>/expenses/periods/<int:period_id>/expenses/", CommonExpenseListCreateView.as_view(), name="common-list"),
    path("spaces/<int:space_id>/expenses/periods/<int:period_id>/expenses/<int:expense_id>/", CommonExpenseDetailView.as_view(), name="common-detail"),
    path("spaces/<int:space_id>/expenses/periods/<int:period_id>/personal-expenses/", PersonalExpenseListCreateView.as_view(), name="personal-list"),
    path("spaces/<int:space_id>/expenses/periods/<int:period_id>/personal-expenses/<int:expense_id>/", PersonalExpenseDetailView.as_view(), name="personal-detail"),
    path("spaces/<int:space_id>/expenses/monthly-reports/", MonthlyExpenseReportListCreateView.as_view(), name="monthly-report-list"),
    path("spaces/<int:space_id>/expenses/monthly-reports/<int:report_id>/", MonthlyExpenseReportDetailView.as_view(), name="monthly-report-detail"),
    path("spaces/<int:space_id>/expenses/monthly-reports/<int:report_id>/regenerate/", MonthlyExpenseReportRegenerateView.as_view(), name="monthly-report-regenerate"),
]
