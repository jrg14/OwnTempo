from decimal import Decimal

from rest_framework import serializers

from apps.spaces.models import Membership, Space

from .models import CommonExpense, ExpenseCategory, ExpenseParticipant, ExpensePeriod, PersonalExpense
from .services import (
    ExpenseOperationError,
    create_common_expense,
    create_period,
    create_personal_expense,
    update_common_expense,
    update_period_configuration,
    update_personal_expense,
)


class ExpenseUserSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(read_only=True)
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)


class ExpenseCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseCategory
        fields = ("id", "name", "color", "is_active", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("El nombre no puede estar vacío.")
        queryset = ExpenseCategory.objects.filter(space=self.context["space"], name=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError("Ya existe una categoría con ese nombre.")
        return value

    def create(self, validated_data):
        return ExpenseCategory.objects.create(space=self.context["space"], **validated_data)


class ExpenseParticipantInputSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    income = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0.00"))
    personal_starting_savings = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0.00"), default=Decimal("0.00"))
    custom_percentage = serializers.DecimalField(max_digits=5, decimal_places=2, min_value=Decimal("0.00"), max_value=Decimal("100.00"), default=Decimal("50.00"))


class ExpenseParticipantSerializer(serializers.ModelSerializer):
    user = ExpenseUserSerializer(read_only=True)

    class Meta:
        model = ExpenseParticipant
        fields = ("id", "user", "income", "personal_starting_savings", "custom_percentage", "position")
        read_only_fields = fields


class ExpensePeriodSerializer(serializers.ModelSerializer):
    participants = ExpenseParticipantSerializer(many=True, read_only=True)
    participant_inputs = ExpenseParticipantInputSerializer(many=True, write_only=True, source="participants", required=False)

    class Meta:
        model = ExpensePeriod
        fields = (
            "id", "space_id", "year", "month", "split_mode", "status",
            "participants", "participant_inputs", "created_at", "updated_at",
        )
        read_only_fields = ("id", "space_id", "created_at", "updated_at")

    def validate(self, attrs):
        participants = attrs.get("participants")
        expected_count = 1 if self.context["space"].kind == Space.Kind.PERSONAL else 2
        if self.instance is None and participants is None:
            raise serializers.ValidationError({"participant_inputs": f"Selecciona {expected_count} participante(s)."})
        if self.instance is None and ExpensePeriod.objects.filter(space=self.context["space"], year=attrs.get("year"), month=attrs.get("month")).exists():
            raise serializers.ValidationError({"month": "Ya existe un periodo para este mes."})
        if self.instance and ({"year", "month"} & set(attrs)):
            raise serializers.ValidationError({"month": "No se puede cambiar el mes de un periodo existente."})
        if self.instance and self.instance.status == ExpensePeriod.Status.CLOSED:
            only_reopening = set(attrs) == {"status"} and attrs.get("status") == ExpensePeriod.Status.OPEN
            if not only_reopening:
                raise serializers.ValidationError({"detail": "El periodo está cerrado."})
        if participants is not None:
            if len(participants) != expected_count or len({item["user_id"] for item in participants}) != expected_count:
                raise serializers.ValidationError({"participant_inputs": f"Selecciona exactamente {expected_count} participante(s)."})
            member_ids = set(Membership.objects.filter(space=self.context["space"], user_id__in=[item["user_id"] for item in participants]).values_list("user_id", flat=True))
            if member_ids != {item["user_id"] for item in participants}:
                raise serializers.ValidationError({"participant_inputs": "Todos deben pertenecer al espacio."})
        mode = attrs.get("split_mode", self.instance.split_mode if self.instance else ExpensePeriod.SplitMode.INCOME)
        effective = participants
        if effective is None and self.instance:
            effective = [
                {"income": item.income, "custom_percentage": item.custom_percentage}
                for item in self.instance.participants.all()
            ]
        if self.context["space"].kind == Space.Kind.SHARED and effective and mode == ExpensePeriod.SplitMode.INCOME and sum((item["income"] for item in effective), Decimal("0.00")) <= 0:
            raise serializers.ValidationError({"participant_inputs": "Indica al menos un ingreso positivo."})
        if effective and mode == ExpensePeriod.SplitMode.CUSTOM and sum((item["custom_percentage"] for item in effective), Decimal("0.00")) != Decimal("100.00"):
            raise serializers.ValidationError({"participant_inputs": "Los porcentajes deben sumar 100%."})
        if self.instance and self.instance.status == ExpensePeriod.Status.CLOSED and attrs.get("status") == ExpensePeriod.Status.OPEN:
            membership = Membership.objects.get(space=self.context["space"], user=self.context["request"].user)
            if membership.role != Membership.Role.OWNER:
                raise serializers.ValidationError({"status": "Solo el propietario puede reabrir el periodo."})
        return attrs

    def create(self, validated_data):
        try:
            return create_period(self.context["request"].user, self.context["space"], validated_data)
        except ExpenseOperationError as error:
            raise serializers.ValidationError({"detail": str(error)}) from error

    def update(self, instance, validated_data):
        try:
            return update_period_configuration(instance, validated_data)
        except ExpenseOperationError as error:
            raise serializers.ValidationError({"detail": str(error)}) from error


class ExpenseCategorySummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseCategory
        fields = ("id", "name", "color")
        read_only_fields = fields


class CommonExpenseSerializer(serializers.ModelSerializer):
    category = ExpenseCategorySummarySerializer(read_only=True)
    category_id = serializers.IntegerField(write_only=True)
    paid_by = ExpenseParticipantSerializer(read_only=True)
    paid_by_id = serializers.IntegerField(write_only=True)
    created_by = ExpenseUserSerializer(read_only=True)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0.01"))

    class Meta:
        model = CommonExpense
        fields = (
            "id", "description", "amount", "spent_on", "category", "category_id",
            "paid_by", "paid_by_id", "created_by", "created_at", "updated_at",
        )
        read_only_fields = ("id", "created_by", "created_at", "updated_at")

    def validate(self, attrs):
        period = self.context["period"]
        category_id = attrs.pop("category_id", self.instance.category_id if self.instance else None)
        paid_by_id = attrs.pop("paid_by_id", self.instance.paid_by_id if self.instance else None)
        try:
            attrs["category"] = ExpenseCategory.objects.get(pk=category_id, space=period.space)
        except ExpenseCategory.DoesNotExist as error:
            raise serializers.ValidationError({"category_id": "La categoría no está disponible."}) from error
        if not attrs["category"].is_active and (self.instance is None or self.instance.category_id != category_id):
            raise serializers.ValidationError({"category_id": "La categoría no está activa."})
        try:
            attrs["paid_by"] = period.participants.get(pk=paid_by_id)
        except ExpenseParticipant.DoesNotExist as error:
            raise serializers.ValidationError({"paid_by_id": "La persona no pertenece al periodo."}) from error
        spent_on = attrs.get("spent_on", self.instance.spent_on if self.instance else None)
        if spent_on and (spent_on.year != period.year or spent_on.month != period.month):
            raise serializers.ValidationError({"spent_on": "La fecha debe pertenecer al mes del periodo."})
        return attrs

    def create(self, validated_data):
        try:
            return create_common_expense(self.context["request"].user, self.context["period"], validated_data)
        except ExpenseOperationError as error:
            raise serializers.ValidationError({"detail": str(error)}) from error

    def update(self, instance, validated_data):
        try:
            return update_common_expense(instance, validated_data)
        except ExpenseOperationError as error:
            raise serializers.ValidationError({"detail": str(error)}) from error


class PersonalExpenseSerializer(serializers.ModelSerializer):
    category = ExpenseCategorySummarySerializer(read_only=True)
    category_id = serializers.IntegerField(write_only=True)
    owner = ExpenseParticipantSerializer(read_only=True)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0.01"))

    class Meta:
        model = PersonalExpense
        fields = ("id", "description", "amount", "spent_on", "category", "category_id", "owner", "created_at", "updated_at")
        read_only_fields = ("id", "owner", "created_at", "updated_at")

    def validate(self, attrs):
        period = self.context["period"]
        category_id = attrs.pop("category_id", self.instance.category_id if self.instance else None)
        try:
            attrs["category"] = ExpenseCategory.objects.get(pk=category_id, space=period.space)
        except ExpenseCategory.DoesNotExist as error:
            raise serializers.ValidationError({"category_id": "La categoría no está disponible."}) from error
        if not attrs["category"].is_active and (self.instance is None or self.instance.category_id != category_id):
            raise serializers.ValidationError({"category_id": "La categoría no está activa."})
        spent_on = attrs.get("spent_on", self.instance.spent_on if self.instance else None)
        if spent_on and (spent_on.year != period.year or spent_on.month != period.month):
            raise serializers.ValidationError({"spent_on": "La fecha debe pertenecer al mes del periodo."})
        return attrs

    def create(self, validated_data):
        try:
            return create_personal_expense(self.context["request"].user, self.context["period"], validated_data)
        except (ExpenseOperationError, ExpenseParticipant.DoesNotExist) as error:
            raise serializers.ValidationError({"detail": str(error) or "No participas en este periodo."}) from error

    def update(self, instance, validated_data):
        try:
            return update_personal_expense(instance, validated_data)
        except ExpenseOperationError as error:
            raise serializers.ValidationError({"detail": str(error)}) from error
