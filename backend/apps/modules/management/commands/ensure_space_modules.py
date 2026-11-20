from django.core.management.base import BaseCommand

from apps.modules.services import ensure_space_modules
from apps.spaces.models import Space


class Command(BaseCommand):
    help = "Crea las configuraciones de módulos que falten en los espacios."

    def handle(self, *args, **options):
        created = 0
        for space in Space.objects.iterator():
            before = space.module_configurations.count()
            ensure_space_modules(space)
            created += len(space.module_configurations.all()) - before

        self.stdout.write(
            self.style.SUCCESS(f"Configuraciones de módulos creadas: {created}.")
        )
