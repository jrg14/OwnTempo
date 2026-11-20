from rest_framework.permissions import BasePermission

from .catalog import get_module_definition
from .models import SpaceModule


class HasActiveModule(BasePermission):
    message = "Este módulo no está disponible en el espacio."

    def has_permission(self, request, view):
        module_key = getattr(view, "module_key", None) or view.kwargs.get(
            "module_key"
        )
        definition = get_module_definition(module_key)
        if definition is None or not definition.available:
            return False

        return SpaceModule.objects.filter(
            space_id=view.kwargs.get("space_id"),
            module_key=module_key,
            enabled=True,
        ).exists()
