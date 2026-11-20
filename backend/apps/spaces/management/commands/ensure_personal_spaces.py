from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apps.spaces.models import Space
from apps.spaces.services import ensure_personal_space


class Command(BaseCommand):
    help = "Crea los espacios personales que falten para los usuarios existentes."

    def handle(self, *args, **options):
        user_model = get_user_model()
        users = user_model.objects.exclude(
            created_spaces__kind=Space.Kind.PERSONAL,
        ).iterator()
        created = 0

        for user in users:
            ensure_personal_space(user)
            created += 1

        self.stdout.write(
            self.style.SUCCESS(f"Espacios personales creados: {created}.")
        )
