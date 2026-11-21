from django.db import transaction

from apps.spaces.models import Space

from .catalog import MODULE_CATALOG
from .models import SpaceModule


@transaction.atomic
def ensure_space_modules(space):
    configurations = []
    for definition in MODULE_CATALOG:
        enabled_by_default = not (
            definition.personal_only and space.kind != Space.Kind.PERSONAL
        )
        configuration, _created = SpaceModule.objects.get_or_create(
            space=space,
            module_key=definition.key,
            defaults={"enabled": enabled_by_default},
        )
        if definition.personal_only and not enabled_by_default and configuration.enabled:
            configuration.enabled = False
            configuration.save(update_fields=("enabled", "updated_at"))
        configurations.append(configuration)
    return configurations
