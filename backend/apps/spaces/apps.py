from django.apps import AppConfig


class SpacesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.spaces"
    verbose_name = "Espacios"

    def ready(self):
        from . import signals  # noqa: F401
