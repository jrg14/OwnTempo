from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.modules.models import SpaceModule
from apps.spaces.models import Membership
from apps.spaces.services import create_shared_space

from .models import CommonExpense, PersonalExpense
from .services import (
    ExpenseOperationError,
    calculate_period_summary,
    create_common_expense,
    create_period,
    create_personal_expense,
)


class ExpenseCalculationTests(APITestCase):
    def setUp(self):
        users = get_user_model()
        self.owner = users.objects.create_user(username="ana", password="secret")
        self.member = users.objects.create_user(username="luis", password="secret")
        self.space = create_shared_space(self.owner, "Casa")
        Membership.objects.create(user=self.member, space=self.space, role=Membership.Role.MEMBER)
        self.period = create_period(self.owner, self.space, {
            "year": 2026,
            "month": 11,
            "split_mode": "income",
            "participants": [
                {"user_id": self.owner.id, "income": Decimal("3000.00"), "personal_starting_savings": Decimal("500.00"), "custom_percentage": Decimal("50.00")},
                {"user_id": self.member.id, "income": Decimal("2000.00"), "personal_starting_savings": Decimal("250.00"), "custom_percentage": Decimal("50.00")},
            ],
        })
        self.category = self.space.expense_categories.get(name="Vivienda")
        self.owner_participant = self.period.participants.get(user=self.owner)
        self.member_participant = self.period.participants.get(user=self.member)

    def test_income_split_settlement_and_personal_savings(self):
        create_common_expense(self.owner, self.period, {
            "category": self.category, "description": "Alquiler", "amount": Decimal("800.00"),
            "spent_on": date(2026, 11, 1), "paid_by": self.owner_participant,
        })
        create_common_expense(self.member, self.period, {
            "category": self.category, "description": "Seguro", "amount": Decimal("200.00"),
            "spent_on": date(2026, 11, 2), "paid_by": self.member_participant,
        })
        create_personal_expense(self.owner, self.period, {
            "category": self.category, "description": "Libro", "amount": Decimal("300.00"),
            "spent_on": date(2026, 11, 3),
        })

        summary = calculate_period_summary(self.period)
        owner = next(item for item in summary["participants"] if item["participant"].user_id == self.owner.id)
        member = next(item for item in summary["participants"] if item["participant"].user_id == self.member.id)

        self.assertEqual(summary["total_common"], Decimal("1000.00"))
        self.assertEqual(owner["expected_contribution"], Decimal("600.00"))
        self.assertEqual(member["expected_contribution"], Decimal("400.00"))
        self.assertEqual(owner["difference"], Decimal("-200.00"))
        self.assertEqual(summary["transfers"][0]["from"].user_id, self.member.id)
        self.assertEqual(summary["transfers"][0]["amount"], Decimal("200.00"))
        self.assertEqual(owner["available_savings"], Decimal("2400.00"))
        self.assertEqual(owner["personal_starting_savings"], Decimal("500.00"))
        self.assertEqual(owner["final_savings"], Decimal("200.00"))

    def test_cent_rounding_preserves_total(self):
        self.period.split_mode = "equal"
        self.period.save()
        create_common_expense(self.owner, self.period, {
            "category": self.category, "description": "Céntimo", "amount": Decimal("0.01"),
            "spent_on": date(2026, 11, 1), "paid_by": self.owner_participant,
        })
        summary = calculate_period_summary(self.period)
        contributions = [item["expected_contribution"] for item in summary["participants"]]
        self.assertEqual(sum(contributions), Decimal("0.01"))
        self.assertEqual(contributions, [Decimal("0.01"), Decimal("0.00")])

    def test_personal_expense_cannot_exceed_available_savings(self):
        with self.assertRaises(ExpenseOperationError):
            create_personal_expense(self.owner, self.period, {
                "category": self.category, "description": "Imposible", "amount": Decimal("3000.01"),
                "spent_on": date(2026, 11, 3),
            })
        self.assertFalse(PersonalExpense.objects.filter(description="Imposible").exists())


class ExpenseApiTests(APITestCase):
    def setUp(self):
        users = get_user_model()
        self.owner = users.objects.create_user(username="ana", password="secret")
        self.member = users.objects.create_user(username="luis", password="secret")
        self.outsider = users.objects.create_user(username="marta", password="secret")
        self.space = create_shared_space(self.owner, "Casa")
        Membership.objects.create(user=self.member, space=self.space, role=Membership.Role.MEMBER)
        self.period_url = reverse("expenses:period-list", args=(self.space.id,))
        self.client.force_authenticate(self.owner)
        response = self.client.post(self.period_url, {
            "year": 2026, "month": 11, "split_mode": "income",
            "participant_inputs": [
                {"user_id": self.owner.id, "income": "3000.00", "personal_starting_savings": "500.00", "custom_percentage": "50.00"},
                {"user_id": self.member.id, "income": "2000.00", "personal_starting_savings": "250.00", "custom_percentage": "50.00"},
            ],
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.period_id = response.data["id"]
        self.category_id = self.space.expense_categories.get(name="Vivienda").id

    def test_common_expense_summary_and_isolation(self):
        participant_id = self.space.expense_periods.get(pk=self.period_id).participants.get(user=self.owner).id
        common_url = reverse("expenses:common-list", args=(self.space.id, self.period_id))
        created = self.client.post(common_url, {
            "description": "Alquiler", "amount": "1000.00", "spent_on": "2026-11-01",
            "category_id": self.category_id, "paid_by_id": participant_id,
        }, format="json")
        summary = self.client.get(reverse("expenses:summary", args=(self.space.id, self.period_id)))
        self.assertEqual(created.status_code, status.HTTP_201_CREATED, created.data)
        self.assertEqual(summary.status_code, status.HTTP_200_OK)
        self.assertEqual(summary.data["total_common"], "1000.00")

        self.client.force_authenticate(self.outsider)
        self.assertEqual(self.client.get(common_url).status_code, status.HTTP_403_FORBIDDEN)

    def test_personal_details_are_private_but_totals_are_shared(self):
        personal_url = reverse("expenses:personal-list", args=(self.space.id, self.period_id))
        created = self.client.post(personal_url, {
            "description": "Libro", "amount": "25.00", "spent_on": "2026-11-02", "category_id": self.category_id,
        }, format="json")
        self.assertEqual(created.status_code, status.HTTP_201_CREATED, created.data)

        self.client.force_authenticate(self.member)
        own_list = self.client.get(personal_url)
        summary = self.client.get(reverse("expenses:summary", args=(self.space.id, self.period_id)))
        owner_total = next(item for item in summary.data["participants"] if item["user"]["id"] == self.owner.id)
        self.assertEqual(own_list.data, [])
        self.assertEqual(owner_total["personal_spent"], "25.00")

    def test_closed_and_disabled_period_block_changes_without_deleting_data(self):
        detail = reverse("expenses:period-detail", args=(self.space.id, self.period_id))
        closed = self.client.patch(detail, {"status": "closed"}, format="json")
        self.assertEqual(closed.status_code, status.HTTP_200_OK)
        common_url = reverse("expenses:common-list", args=(self.space.id, self.period_id))
        self.assertEqual(self.client.post(common_url, {}, format="json").status_code, status.HTTP_400_BAD_REQUEST)

        SpaceModule.objects.filter(space=self.space, module_key="expenses").update(enabled=False)
        self.assertEqual(self.client.get(self.period_url).status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(self.space.expense_periods.filter(pk=self.period_id).exists())

    def test_duplicate_period_and_invalid_date_are_rejected(self):
        duplicate = self.client.post(self.period_url, {
            "year": 2026, "month": 11, "split_mode": "equal",
            "participant_inputs": [
                {"user_id": self.owner.id, "income": "1.00", "custom_percentage": "50.00"},
                {"user_id": self.member.id, "income": "1.00", "custom_percentage": "50.00"},
            ],
        }, format="json")
        self.assertEqual(duplicate.status_code, status.HTTP_400_BAD_REQUEST)

        participant_id = self.space.expense_periods.get(pk=self.period_id).participants.get(user=self.owner).id
        invalid = self.client.post(reverse("expenses:common-list", args=(self.space.id, self.period_id)), {
            "description": "Otro mes", "amount": "10.00", "spent_on": "2026-12-01",
            "category_id": self.category_id, "paid_by_id": participant_id,
        }, format="json")
        self.assertEqual(invalid.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(CommonExpense.objects.filter(description="Otro mes").exists())


class PersonalSpaceExpenseApiTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="ana", password="secret")
        self.space = self.user.created_spaces.get(kind="personal")
        self.client.force_authenticate(self.user)

    def test_personal_space_uses_one_participant_and_manual_balance(self):
        created_period = self.client.post(
            reverse("expenses:period-list", args=(self.space.id,)),
            {
                "year": 2026,
                "month": 11,
                "split_mode": "equal",
                "participant_inputs": [{
                    "user_id": self.user.id,
                    "income": "0.00",
                    "personal_starting_savings": "300.00",
                    "custom_percentage": "100.00",
                }],
            },
            format="json",
        )
        self.assertEqual(created_period.status_code, status.HTTP_201_CREATED, created_period.data)
        period_id = created_period.data["id"]
        category = self.space.expense_categories.get(name="Ocio")

        personal = self.client.post(
            reverse("expenses:personal-list", args=(self.space.id, period_id)),
            {
                "description": "Cine",
                "amount": "25.00",
                "spent_on": "2026-11-10",
                "category_id": category.id,
            },
            format="json",
        )
        summary = self.client.get(reverse("expenses:summary", args=(self.space.id, period_id)))

        self.assertEqual(personal.status_code, status.HTTP_201_CREATED, personal.data)
        self.assertEqual(summary.status_code, status.HTTP_200_OK)
        self.assertEqual(summary.data["participants"][0]["personal_starting_savings"], "300.00")
        self.assertEqual(summary.data["participants"][0]["final_savings"], "275.00")

    def test_personal_space_rejects_common_expenses(self):
        period = create_period(self.user, self.space, {
            "year": 2026,
            "month": 11,
            "split_mode": "equal",
            "participants": [{
                "user_id": self.user.id,
                "income": Decimal("0.00"),
                "personal_starting_savings": Decimal("100.00"),
                "custom_percentage": Decimal("100.00"),
            }],
        })
        category = self.space.expense_categories.get(name="Otros")
        response = self.client.post(
            reverse("expenses:common-list", args=(self.space.id, period.id)),
            {
                "description": "No permitido",
                "amount": "10.00",
                "spent_on": "2026-11-10",
                "category_id": category.id,
                "paid_by_id": period.participants.get().id,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
