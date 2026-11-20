from django.db import transaction

from .catalog import MODULE_KEYS
from .models import SpaceModule


@transaction.atomic
def ensure_space_modules(space):
    configurations = []
    for module_key in MODULE_KEYS:
        configuration, _created = SpaceModule.objects.get_or_create(
            space=space,
            module_key=module_key,
            defaults={"enabled": True},
        )
        configurations.append(configuration)
    return configurations
