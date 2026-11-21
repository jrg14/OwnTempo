from django.db import migrations, models


MODULE_KEYS = ("tasks", "shopping", "wishlist", "calendar", "expenses", "training")


def add_training_configuration(apps, schema_editor):
    space_model = apps.get_model("spaces", "Space")
    space_module_model = apps.get_model("modules", "SpaceModule")
    configurations = [
        space_module_model(
            space=space,
            module_key="training",
            enabled=space.kind == "personal",
        )
        for space in space_model.objects.iterator()
    ]
    space_module_model.objects.bulk_create(configurations, ignore_conflicts=True)


class Migration(migrations.Migration):
    dependencies = [("modules", "0002_populate_space_modules")]

    operations = [
        migrations.RemoveConstraint(model_name="spacemodule", name="valid_space_module_key"),
        migrations.AlterField(
            model_name="spacemodule",
            name="module_key",
            field=models.CharField(
                choices=[
                    ("tasks", "Tareas"),
                    ("shopping", "Lista de compras"),
                    ("wishlist", "Lista de deseos"),
                    ("calendar", "Calendario"),
                    ("expenses", "Gastos"),
                    ("training", "Entrenamiento"),
                ],
                max_length=32,
            ),
        ),
        migrations.AddConstraint(
            model_name="spacemodule",
            constraint=models.CheckConstraint(
                condition=models.Q(module_key__in=MODULE_KEYS),
                name="valid_space_module_key",
            ),
        ),
        migrations.RunPython(add_training_configuration, migrations.RunPython.noop),
    ]
