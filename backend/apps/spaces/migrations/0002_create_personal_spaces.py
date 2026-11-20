from django.conf import settings
from django.db import migrations


def create_personal_spaces(apps, schema_editor):
    user_model = apps.get_model(*settings.AUTH_USER_MODEL.split("."))
    space_model = apps.get_model("spaces", "Space")
    membership_model = apps.get_model("spaces", "Membership")

    for user in user_model.objects.iterator():
        space, _created = space_model.objects.get_or_create(
            created_by=user,
            kind="personal",
            defaults={"name": "Mi espacio"},
        )
        membership_model.objects.get_or_create(
            user=user,
            space=space,
            defaults={"role": "owner"},
        )


class Migration(migrations.Migration):
    dependencies = [
        ("spaces", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_personal_spaces, migrations.RunPython.noop),
    ]
