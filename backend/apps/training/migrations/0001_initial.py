import decimal

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("spaces", "0003_invitation"),
    ]

    operations = [
        migrations.CreateModel(
            name="StrengthWorkout",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("workout_date", models.DateField()),
                ("started_at", models.TimeField(blank=True, null=True)),
                ("duration_minutes", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("space", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="spaces.space")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ("-workout_date", "-started_at", "-id")},
        ),
        migrations.CreateModel(
            name="StrengthExercise",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120)),
                ("order", models.PositiveSmallIntegerField(default=1)),
                ("notes", models.TextField(blank=True)),
                ("workout", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="exercises", to="training.strengthworkout")),
            ],
            options={"ordering": ("order", "id")},
        ),
        migrations.CreateModel(
            name="StrengthSet",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("set_number", models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(1)])),
                ("weight_kg", models.DecimalField(decimal_places=2, max_digits=6, validators=[django.core.validators.MinValueValidator(decimal.Decimal("0"))])),
                ("repetitions", models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(1)])),
                ("rest_seconds", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("exercise", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="sets", to="training.strengthexercise")),
            ],
            options={"ordering": ("set_number", "id")},
        ),
        migrations.CreateModel(
            name="TrainingProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("height_cm", models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(80), django.core.validators.MaxValueValidator(250)])),
                ("date_of_birth", models.DateField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("space", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="spaces.space")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="DailySteps",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("date", models.DateField()),
                ("steps", models.PositiveIntegerField()),
                ("goal", models.PositiveIntegerField(blank=True, null=True)),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("space", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="spaces.space")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ("-date", "-id")},
        ),
        migrations.CreateModel(
            name="BodyWeightEntry",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("date", models.DateField()),
                ("weight_kg", models.DecimalField(decimal_places=2, max_digits=5, validators=[django.core.validators.MinValueValidator(decimal.Decimal("20")), django.core.validators.MaxValueValidator(decimal.Decimal("500"))])),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("space", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="spaces.space")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ("-date", "-id")},
        ),
        migrations.AddIndex(model_name="strengthworkout", index=models.Index(fields=["space", "user", "workout_date"], name="training_workout_date_idx")),
        migrations.AddConstraint(model_name="strengthexercise", constraint=models.UniqueConstraint(fields=("workout", "order"), name="unique_exercise_order")),
        migrations.AddConstraint(model_name="strengthset", constraint=models.UniqueConstraint(fields=("exercise", "set_number"), name="unique_strength_set_number")),
        migrations.AddConstraint(model_name="trainingprofile", constraint=models.UniqueConstraint(fields=("space", "user"), name="unique_training_profile")),
        migrations.AddIndex(model_name="dailysteps", index=models.Index(fields=["space", "user", "date"], name="training_steps_date_idx")),
        migrations.AddConstraint(model_name="dailysteps", constraint=models.UniqueConstraint(fields=("space", "user", "date"), name="unique_daily_steps")),
        migrations.AddIndex(model_name="bodyweightentry", index=models.Index(fields=["space", "user", "date"], name="training_weight_date_idx")),
        migrations.AddConstraint(model_name="bodyweightentry", constraint=models.UniqueConstraint(fields=("space", "user", "date"), name="unique_body_weight")),
    ]
