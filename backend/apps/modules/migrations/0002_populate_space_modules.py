from django.db import migrations


MODULE_KEYS = ("tasks", "shopping", "wishlist", "calendar", "expenses")


def populate_space_modules(apps, schema_editor):
    space_model = apps.get_model("spaces", "Space")
    space_module_model = apps.get_model("modules", "SpaceModule")

    configurations = [
        space_module_model(space=space, module_key=module_key, enabled=True)
        for space in space_model.objects.iterator()
        for module_key in MODULE_KEYS
    ]
    space_module_model.objects.bulk_create(configurations, ignore_conflicts=True)


class Migration(migrations.Migration):
    dependencies = [
        ("modules", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(populate_space_modules, migrations.RunPython.noop),
    ]
