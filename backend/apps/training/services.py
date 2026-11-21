from django.db import transaction

from .models import StrengthExercise, StrengthSet, StrengthWorkout


def _replace_exercises(workout, exercises_data):
    workout.exercises.all().delete()
    for exercise_position, exercise_data in enumerate(exercises_data, start=1):
        sets_data = exercise_data.pop("sets")
        exercise = StrengthExercise.objects.create(
            workout=workout,
            order=exercise_data.pop("order", exercise_position),
            **exercise_data,
        )
        for set_position, set_data in enumerate(sets_data, start=1):
            StrengthSet.objects.create(
                exercise=exercise,
                set_number=set_data.pop("set_number", set_position),
                **set_data,
            )


@transaction.atomic
def create_workout(user, space, validated_data):
    exercises_data = validated_data.pop("exercises")
    workout = StrengthWorkout.objects.create(space=space, user=user, **validated_data)
    _replace_exercises(workout, exercises_data)
    return workout


@transaction.atomic
def update_workout(workout, validated_data):
    workout = StrengthWorkout.objects.select_for_update().get(pk=workout.pk)
    exercises_data = validated_data.pop("exercises", None)
    for field, value in validated_data.items():
        setattr(workout, field, value)
    workout.save()
    if exercises_data is not None:
        _replace_exercises(workout, exercises_data)
    return workout
