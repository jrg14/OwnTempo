from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.modules.models import SpaceModule
from apps.spaces.models import Space
from apps.spaces.services import create_shared_space

from .models import (
    DailySteps,
    HealthMeasurement,
    MonthlyTrainingReport,
    StrengthExercise,
    StrengthSet,
    StrengthWorkout,
    TrainingProfile,
)
from .monthly_reports import build_monthly_context, claim_pending_report, generate_monthly_report


def health_payload(measured_on):
    return {
        "date": measured_on.isoformat(),
        "weight_kg": "79.50",
        "bmi": "24.30",
        "body_fat_percentage": "19.20",
        "subcutaneous_fat_percentage": "16.40",
        "visceral_fat_level": "7.00",
        "body_water_percentage": "57.80",
        "muscle_mass_kg": "60.10",
        "bone_mass_kg": "3.20",
        "basal_metabolic_rate_kcal": 1760,
        "metabolic_age": 34,
    }


class TrainingApiTests(APITestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(username="ana", password="secret")
        self.other = user_model.objects.create_user(username="marta", password="secret")
        self.space = Space.objects.get(created_by=self.user, kind=Space.Kind.PERSONAL)
        self.client.force_authenticate(self.user)

    def test_profile_can_be_created_and_updated(self):
        url = reverse("training:profile", args=(self.space.id,))
        response = self.client.put(url, {"height_cm": 168, "date_of_birth": "1992-06-15"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["height_cm"], 168)
        response = self.client.put(url, {"height_cm": 169, "date_of_birth": "1992-06-15"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(TrainingProfile.objects.get().height_cm, 169)

    def test_profile_rejects_invalid_values(self):
        response = self.client.put(
            reverse("training:profile", args=(self.space.id,)),
            {"height_cm": 20, "date_of_birth": date.today().isoformat()},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_workout_with_exercises_and_sets_is_created(self):
        response = self.client.post(
            reverse("training:workout-list", args=(self.space.id,)),
            {
                "workout_date": date.today().isoformat(),
                "duration_minutes": 45,
                "exercises": [{
                    "name": "Press banca",
                    "order": 1,
                    "sets": [
                        {"set_number": 1, "weight_kg": "60.00", "repetitions": 10},
                        {"set_number": 2, "weight_kg": "70.00", "repetitions": 8},
                    ],
                }],
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(StrengthWorkout.objects.count(), 1)
        self.assertEqual(len(response.data["exercises"][0]["sets"]), 2)

    def test_workout_rejects_invalid_repetitions(self):
        response = self.client.post(
            reverse("training:workout-list", args=(self.space.id,)),
            {
                "workout_date": date.today().isoformat(),
                "exercises": [{"name": "Sentadilla", "order": 1, "sets": [{"set_number": 1, "weight_kg": "80", "repetitions": 0}]}],
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_daily_steps_and_health_are_unique_per_date(self):
        steps_url = reverse("training:steps-list", args=(self.space.id,))
        health_url = reverse("training:health-list", args=(self.space.id,))
        payload_date = date.today().isoformat()
        self.assertEqual(self.client.post(steps_url, {"date": payload_date, "steps": 8000}, format="json").status_code, 201)
        self.assertEqual(self.client.post(steps_url, {"date": payload_date, "steps": 9000}, format="json").status_code, 400)
        self.assertEqual(self.client.post(health_url, health_payload(date.today()), format="json").status_code, 201)
        self.assertEqual(self.client.post(health_url, health_payload(date.today()), format="json").status_code, 400)

    def test_health_measurement_requires_all_scale_metrics(self):
        payload = health_payload(date.today())
        payload.pop("body_water_percentage")

        response = self.client.post(
            reverse("training:health-list", args=(self.space.id,)),
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("body_water_percentage", response.data)

    def test_shared_space_is_rejected_and_training_is_hidden(self):
        shared = create_shared_space(self.user, "Casa")
        self.assertFalse(SpaceModule.objects.get(space=shared, module_key="training").enabled)
        modules = self.client.get(reverse("modules:space-module-list", args=(shared.id,)))
        self.assertNotIn("training", [item["key"] for item in modules.data])
        response = self.client.get(reverse("training:summary", args=(shared.id,)))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_other_user_cannot_access_personal_training(self):
        self.client.force_authenticate(self.other)
        response = self.client.get(reverse("training:summary", args=(self.space.id,)))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_disabled_module_is_rejected(self):
        SpaceModule.objects.filter(space=self.space, module_key="training").update(enabled=False)
        response = self.client.get(reverse("training:summary", args=(self.space.id,)))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_summary_calculates_week_and_health_changes(self):
        today = date.today()
        DailySteps.objects.create(space=self.space, user=self.user, date=today, steps=8000, goal=10000)
        DailySteps.objects.create(space=self.space, user=self.user, date=today - timedelta(days=1), steps=6000)
        first = health_payload(today - timedelta(days=2))
        first["weight_kg"] = "80.00"
        HealthMeasurement.objects.create(space=self.space, user=self.user, **first)
        HealthMeasurement.objects.create(space=self.space, user=self.user, **health_payload(today))
        response = self.client.get(reverse("training:summary", args=(self.space.id,)))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["week"]["total_steps"], 14000)
        self.assertEqual(response.data["health"]["weight_change_from_first_kg"], Decimal("-0.50"))
        self.assertEqual(response.data["health"]["latest"]["metabolic_age"], 34)
        self.assertEqual(len(response.data["health_history"]), 2)


class MonthlyTrainingReportTests(APITestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(username="informe", password="secret")
        self.other = user_model.objects.create_user(username="intruso", password="secret")
        self.space = Space.objects.get(created_by=self.user, kind=Space.Kind.PERSONAL)
        self.client.force_authenticate(self.user)
        self.month = date.today().replace(day=1)

    def create_month_data(self):
        TrainingProfile.objects.create(
            space=self.space,
            user=self.user,
            height_cm=170,
            date_of_birth=date(1990, 5, 10),
        )
        DailySteps.objects.create(
            space=self.space,
            user=self.user,
            date=date.today(),
            steps=9000,
            goal=8000,
        )
        measurement = health_payload(date.today())
        HealthMeasurement.objects.create(space=self.space, user=self.user, **measurement)
        workout = StrengthWorkout.objects.create(
            space=self.space,
            user=self.user,
            workout_date=date.today(),
            duration_minutes=50,
        )
        exercise = StrengthExercise.objects.create(workout=workout, name="Sentadilla", order=1)
        StrengthSet.objects.create(
            exercise=exercise,
            set_number=1,
            weight_kg="80.00",
            repetitions=10,
        )

    def test_context_uses_backend_calculations_and_goal(self):
        self.create_month_data()

        context = build_monthly_context(
            self.space,
            self.user,
            self.month,
            "Entrenar con constancia",
        )

        self.assertEqual(context["training"]["workout_count"], 1)
        self.assertEqual(context["training"]["total_volume_kg"], 800.0)
        self.assertEqual(context["steps"]["goal_completion_rate"], 1.0)
        self.assertEqual(context["health"]["measurements_count"], 1)
        self.assertEqual(context["goals"]["monthly_goal"], "Entrenar con constancia")
        self.assertIn("comparison_previous_month", context)

    def test_report_can_be_queued_listed_and_deleted(self):
        url = reverse("training:monthly-report-list", args=(self.space.id,))
        response = self.client.post(
            url,
            {"month": self.month.strftime("%Y-%m"), "goal": "Mejorar fuerza"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(response.data["status"], "pending")
        self.assertEqual(response.data["month"], self.month.strftime("%Y-%m"))

        listed = self.client.get(url)
        self.assertEqual(listed.status_code, status.HTTP_200_OK)
        self.assertEqual(len(listed.data), 1)

        detail_url = reverse(
            "training:monthly-report-detail",
            args=(self.space.id, response.data["id"]),
        )
        self.assertEqual(self.client.delete(detail_url).status_code, status.HTTP_204_NO_CONTENT)

    def test_other_user_cannot_read_report(self):
        report = MonthlyTrainingReport.objects.create(
            space=self.space,
            user=self.user,
            month=self.month,
        )
        self.client.force_authenticate(self.other)
        response = self.client.get(
            reverse("training:monthly-report-detail", args=(self.space.id, report.id))
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch("apps.training.monthly_reports.request_local_analysis")
    def test_worker_validates_and_persists_local_analysis(self, request_analysis):
        self.create_month_data()
        request_analysis.return_value = {
            "title": "Un mes constante",
            "summary": "Has entrenado y registrado actividad durante el mes.",
            "overall_status": "on_track",
            "scores": {
                "training": 7,
                "activity": 8,
                "health_tracking": 5,
                "consistency": 7,
            },
            "highlights": ["Cumpliste el objetivo de pasos registrado."],
            "improvements": ["Añade más mediciones para observar tendencias."],
            "next_month_actions": ["Mantén una frecuencia semanal estable."],
            "cautions": ["La tendencia de salud se basa en pocos datos."],
        }
        report = MonthlyTrainingReport.objects.create(
            space=self.space,
            user=self.user,
            month=self.month,
            goal="Ganar constancia",
        )

        report_id = claim_pending_report()
        self.assertEqual(report_id, report.id)
        generated = generate_monthly_report(report_id)

        self.assertEqual(generated.status, MonthlyTrainingReport.Status.COMPLETED)
        self.assertEqual(generated.result_payload["title"], "Un mes constante")
        self.assertEqual(generated.input_payload["goals"]["monthly_goal"], "Ganar constancia")
        self.assertTrue(generated.completed_at)
