from rest_framework.permissions import BasePermission

from apps.spaces.models import Space


class IsPersonalTrainingSpace(BasePermission):
    message = "El entrenamiento solo está disponible en tu espacio personal."

    def has_permission(self, request, view):
        return Space.objects.filter(
            pk=view.kwargs.get("space_id"),
            kind=Space.Kind.PERSONAL,
            created_by=request.user,
        ).exists()
