from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.modules.models import SpaceModule
from apps.spaces.models import Space
from apps.spaces.services import create_shared_space

from .models import DailySteps, HealthMeasurement, StrengthWorkout, TrainingProfile


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
