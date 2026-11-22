from django.contrib import admin

from .models import (
    DailySteps,
    HealthMeasurement,
    MonthlyTrainingReport,
    StrengthExercise,
    StrengthSet,
    StrengthWorkout,
    TrainingProfile,
)

admin.site.register(TrainingProfile)
admin.site.register(StrengthWorkout)
admin.site.register(StrengthExercise)
admin.site.register(StrengthSet)
admin.site.register(DailySteps)
admin.site.register(HealthMeasurement)
admin.site.register(MonthlyTrainingReport)
