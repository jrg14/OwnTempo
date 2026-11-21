import decimal

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("training", "0001_initial")]

    operations = [
        migrations.RenameModel(
            old_name="BodyWeightEntry",
            new_name="HealthMeasurement",
        ),
        migrations.RenameIndex(
            model_name="healthmeasurement",
            old_name="training_weight_date_idx",
            new_name="training_health_date_idx",
        ),
        migrations.RemoveConstraint(
            model_name="healthmeasurement",
            name="unique_body_weight",
        ),
        migrations.AddConstraint(
            model_name="healthmeasurement",
            constraint=models.UniqueConstraint(
                fields=("space", "user", "date"),
                name="unique_health_measurement",
            ),
        ),
        migrations.AddField(
            model_name="healthmeasurement",
            name="bmi",
            field=models.DecimalField(
                blank=True, null=True, max_digits=5, decimal_places=2,
                validators=[django.core.validators.MinValueValidator(decimal.Decimal("5")), django.core.validators.MaxValueValidator(decimal.Decimal("100"))],
            ),
        ),
        migrations.AddField(
            model_name="healthmeasurement",
            name="body_fat_percentage",
            field=models.DecimalField(
                blank=True, null=True, max_digits=5, decimal_places=2,
                validators=[django.core.validators.MinValueValidator(decimal.Decimal("0")), django.core.validators.MaxValueValidator(decimal.Decimal("100"))],
            ),
        ),
        migrations.AddField(
            model_name="healthmeasurement",
            name="subcutaneous_fat_percentage",
            field=models.DecimalField(
                blank=True, null=True, max_digits=5, decimal_places=2,
                validators=[django.core.validators.MinValueValidator(decimal.Decimal("0")), django.core.validators.MaxValueValidator(decimal.Decimal("100"))],
            ),
        ),
        migrations.AddField(
            model_name="healthmeasurement",
            name="visceral_fat_level",
            field=models.DecimalField(
                blank=True, null=True, max_digits=5, decimal_places=2,
                validators=[django.core.validators.MinValueValidator(decimal.Decimal("0")), django.core.validators.MaxValueValidator(decimal.Decimal("100"))],
            ),
        ),
        migrations.AddField(
            model_name="healthmeasurement",
            name="body_water_percentage",
            field=models.DecimalField(
                blank=True, null=True, max_digits=5, decimal_places=2,
                validators=[django.core.validators.MinValueValidator(decimal.Decimal("0")), django.core.validators.MaxValueValidator(decimal.Decimal("100"))],
            ),
        ),
        migrations.AddField(
            model_name="healthmeasurement",
            name="muscle_mass_kg",
            field=models.DecimalField(
                blank=True, null=True, max_digits=5, decimal_places=2,
                validators=[django.core.validators.MinValueValidator(decimal.Decimal("0")), django.core.validators.MaxValueValidator(decimal.Decimal("300"))],
            ),
        ),
        migrations.AddField(
            model_name="healthmeasurement",
            name="bone_mass_kg",
            field=models.DecimalField(
                blank=True, null=True, max_digits=4, decimal_places=2,
                validators=[django.core.validators.MinValueValidator(decimal.Decimal("0")), django.core.validators.MaxValueValidator(decimal.Decimal("30"))],
            ),
        ),
        migrations.AddField(
            model_name="healthmeasurement",
            name="basal_metabolic_rate_kcal",
            field=models.PositiveSmallIntegerField(
                blank=True, null=True,
                validators=[django.core.validators.MinValueValidator(500), django.core.validators.MaxValueValidator(10000)],
            ),
        ),
        migrations.AddField(
            model_name="healthmeasurement",
            name="metabolic_age",
            field=models.PositiveSmallIntegerField(
                blank=True, null=True,
                validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(150)],
            ),
        ),
    ]
