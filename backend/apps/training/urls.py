from django.urls import path

from .views import (
    StepsDetailView,
    StepsListCreateView,
    TrainingProfileView,
    TrainingSummaryView,
    HealthDetailView,
    HealthListCreateView,
    WorkoutDetailView,
    WorkoutListCreateView,
    MonthlyReportDetailView,
    MonthlyReportListCreateView,
    MonthlyReportRegenerateView,
)

app_name = "training"

urlpatterns = [
    path("spaces/<int:space_id>/training/profile/", TrainingProfileView.as_view(), name="profile"),
    path("spaces/<int:space_id>/training/workouts/", WorkoutListCreateView.as_view(), name="workout-list"),
    path("spaces/<int:space_id>/training/workouts/<int:workout_id>/", WorkoutDetailView.as_view(), name="workout-detail"),
    path("spaces/<int:space_id>/training/steps/", StepsListCreateView.as_view(), name="steps-list"),
    path("spaces/<int:space_id>/training/steps/<int:steps_id>/", StepsDetailView.as_view(), name="steps-detail"),
    path("spaces/<int:space_id>/training/health/", HealthListCreateView.as_view(), name="health-list"),
    path("spaces/<int:space_id>/training/health/<int:measurement_id>/", HealthDetailView.as_view(), name="health-detail"),
    path("spaces/<int:space_id>/training/summary/", TrainingSummaryView.as_view(), name="summary"),
    path(
        "spaces/<int:space_id>/training/monthly-reports/",
        MonthlyReportListCreateView.as_view(),
        name="monthly-report-list",
    ),
    path(
        "spaces/<int:space_id>/training/monthly-reports/<int:report_id>/",
        MonthlyReportDetailView.as_view(),
        name="monthly-report-detail",
    ),
    path(
        "spaces/<int:space_id>/training/monthly-reports/<int:report_id>/regenerate/",
        MonthlyReportRegenerateView.as_view(),
        name="monthly-report-regenerate",
    ),
]
