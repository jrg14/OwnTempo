from decimal import Decimal

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("expenses", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="expenseparticipant",
            name="personal_starting_savings",
            field=models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=12),
        ),
        migrations.AddConstraint(
            model_name="expenseparticipant",
            constraint=models.CheckConstraint(
                condition=models.Q(("personal_starting_savings__gte", 0)),
                name="expense_participant_nonnegative_personal_savings",
            ),
        ),
    ]
