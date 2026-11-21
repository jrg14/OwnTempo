from decimal import Decimal, ROUND_DOWN

from django.db import transaction
from django.db.models import Sum

from apps.spaces.models import Membership

from .models import CommonExpense, ExpenseCategory, ExpenseParticipant, ExpensePeriod, PersonalExpense


CENT = Decimal("0.01")
HUNDRED = Decimal("100.00")
DEFAULT_CATEGORIES = (
    ("Vivienda", "teal"),
    ("Alimentación", "amber"),
    ("Suministros", "blue"),
    ("Transporte", "violet"),
    ("Ocio", "rose"),
    ("Otros", "slate"),
)


class ExpenseOperationError(Exception):
    pass


def ensure_default_categories(space):
    if ExpenseCategory.objects.filter(space=space).exists():
        return
    for name, color in DEFAULT_CATEGORIES:
        ExpenseCategory.objects.get_or_create(space=space, name=name, defaults={"color": color})


def _allocate(total, weights, participant_ids):
    if total == 0:
        return {participant_id: Decimal("0.00") for participant_id in participant_ids}
    weight_total = sum(weights, Decimal("0.00"))
    if weight_total <= 0:
        raise ExpenseOperationError("La suma usada para el reparto debe ser mayor que cero.")
    exact = [total * weight / weight_total for weight in weights]
    rounded = [value.quantize(CENT, rounding=ROUND_DOWN) for value in exact]
    remaining_cents = int(((total - sum(rounded, Decimal("0.00"))) / CENT).to_integral_value())
    order = sorted(range(len(exact)), key=lambda index: (exact[index] - rounded[index], -participant_ids[index]), reverse=True)
    for index in order[:remaining_cents]:
        rounded[index] += CENT
    return dict(zip(participant_ids, rounded, strict=True))


def calculate_period_summary(period):
    participants = list(period.participants.select_related("user").order_by("position", "id"))
    expected_count = 1 if period.space.kind == period.space.Kind.PERSONAL else 2
    if len(participants) != expected_count:
        raise ExpenseOperationError(f"El periodo debe tener exactamente {expected_count} participante(s).")
    total = period.common_expenses.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    ids = [participant.id for participant in participants]
    if period.split_mode == ExpensePeriod.SplitMode.EQUAL:
        weights = [Decimal("1"), Decimal("1")]
    elif period.split_mode == ExpensePeriod.SplitMode.INCOME:
        weights = [participant.income for participant in participants]
        if sum(weights, Decimal("0.00")) <= 0:
            raise ExpenseOperationError("Indica al menos un ingreso positivo para el reparto proporcional.")
    else:
        weights = [participant.custom_percentage for participant in participants]
        if sum(weights, Decimal("0.00")) != HUNDRED:
            raise ExpenseOperationError("Los porcentajes personalizados deben sumar 100%.")
    expected = _allocate(total, weights, ids)
    paid_rows = period.common_expenses.values("paid_by_id").annotate(total=Sum("amount"))
    paid = {row["paid_by_id"]: row["total"] for row in paid_rows}
    personal_rows = period.personal_expenses.values("owner_id").annotate(total=Sum("amount"))
    personal = {row["owner_id"]: row["total"] for row in personal_rows}
    participant_summaries = []
    debtors = []
    creditors = []
    for participant in participants:
        expected_amount = expected[participant.id]
        paid_amount = paid.get(participant.id, Decimal("0.00"))
        difference = expected_amount - paid_amount
        available = participant.income - expected_amount
        personal_spent = personal.get(participant.id, Decimal("0.00"))
        final_savings = participant.personal_starting_savings - personal_spent
        participant_summaries.append({
            "participant": participant,
            "income": participant.income,
            "expected_contribution": expected_amount,
            "paid": paid_amount,
            "difference": difference,
            "available_savings": available,
            "personal_starting_savings": participant.personal_starting_savings,
            "personal_spent": personal_spent,
            "final_savings": final_savings,
        })
        if difference > 0:
            debtors.append((participant, difference))
        elif difference < 0:
            creditors.append((participant, -difference))
    transfers = []
    if debtors and creditors:
        transfers.append({"from": debtors[0][0], "to": creditors[0][0], "amount": min(debtors[0][1], creditors[0][1])})
    category_rows = period.common_expenses.values("category_id", "category__name", "category__color").annotate(total=Sum("amount")).order_by("category__name")
    return {
        "total_common": total,
        "categories": list(category_rows),
        "participants": participant_summaries,
        "transfers": transfers,
    }


def validate_savings(period):
    summary = calculate_period_summary(period)
    for item in summary["participants"]:
        if item["final_savings"] < 0:
            raise ExpenseOperationError(f'Los gastos personales de {item["participant"].user.get_username()} superan su saldo personal inicial.')
    return summary


@transaction.atomic
def create_period(user, space, validated_data):
    participant_data = validated_data.pop("participants")
    expected_count = 1 if space.kind == space.Kind.PERSONAL else 2
    if len(participant_data) != expected_count or len({item["user_id"] for item in participant_data}) != expected_count:
        raise ExpenseOperationError(f"Selecciona exactamente {expected_count} participante(s).")
    member_ids = set(Membership.objects.filter(space=space, user_id__in=[item["user_id"] for item in participant_data]).values_list("user_id", flat=True))
    if member_ids != {item["user_id"] for item in participant_data}:
        raise ExpenseOperationError("Todos los participantes deben pertenecer al espacio.")
    period = ExpensePeriod(space=space, created_by=user, **validated_data)
    period.save()
    for position, data in enumerate(participant_data):
        ExpenseParticipant.objects.create(period=period, position=position, **data)
    ensure_default_categories(space)
    validate_savings(period)
    return period


@transaction.atomic
def update_period_configuration(period, validated_data):
    period = ExpensePeriod.objects.select_for_update().get(pk=period.pk)
    if period.status == ExpensePeriod.Status.CLOSED:
        only_reopening = set(validated_data) == {"status"} and validated_data["status"] == ExpensePeriod.Status.OPEN
        if not only_reopening:
            raise ExpenseOperationError("El periodo está cerrado.")
    participant_data = validated_data.pop("participants", None)
    for field, value in validated_data.items():
        setattr(period, field, value)
    period.save()
    if participant_data is not None:
        by_user = {participant.user_id: participant for participant in period.participants.select_for_update()}
        if {item["user_id"] for item in participant_data} != set(by_user):
            raise ExpenseOperationError("No se pueden cambiar los participantes de un periodo existente.")
        for item in participant_data:
            participant = by_user[item["user_id"]]
            participant.income = item.get("income", participant.income)
            participant.personal_starting_savings = item.get("personal_starting_savings", participant.personal_starting_savings)
            participant.custom_percentage = item.get("custom_percentage", participant.custom_percentage)
            participant.save()
    validate_savings(period)
    return period


def _ensure_open(period):
    if period.status == ExpensePeriod.Status.CLOSED:
        raise ExpenseOperationError("El periodo está cerrado.")


@transaction.atomic
def create_common_expense(user, period, validated_data):
    period = ExpensePeriod.objects.select_for_update().get(pk=period.pk)
    if period.space.kind == period.space.Kind.PERSONAL:
        raise ExpenseOperationError("Los espacios personales no admiten gastos comunes.")
    _ensure_open(period)
    expense = CommonExpense(period=period, created_by=user, **validated_data)
    expense.save()
    validate_savings(period)
    return expense


@transaction.atomic
def update_common_expense(expense, validated_data):
    expense = CommonExpense.objects.select_for_update().select_related("period").get(pk=expense.pk)
    _ensure_open(expense.period)
    for field, value in validated_data.items():
        setattr(expense, field, value)
    expense.save()
    validate_savings(expense.period)
    return expense


@transaction.atomic
def delete_common_expense(expense):
    expense = CommonExpense.objects.select_for_update().select_related("period").get(pk=expense.pk)
    _ensure_open(expense.period)
    expense.delete()


@transaction.atomic
def create_personal_expense(user, period, validated_data):
    period = ExpensePeriod.objects.select_for_update().get(pk=period.pk)
    _ensure_open(period)
    owner = period.participants.get(user=user)
    expense = PersonalExpense(period=period, owner=owner, created_by=user, **validated_data)
    expense.save()
    validate_savings(period)
    return expense


@transaction.atomic
def update_personal_expense(expense, validated_data):
    expense = PersonalExpense.objects.select_for_update().select_related("period").get(pk=expense.pk)
    _ensure_open(expense.period)
    for field, value in validated_data.items():
        setattr(expense, field, value)
    expense.save()
    validate_savings(expense.period)
    return expense


@transaction.atomic
def delete_personal_expense(expense):
    expense = PersonalExpense.objects.select_for_update().select_related("period").get(pk=expense.pk)
    _ensure_open(expense.period)
    expense.delete()
