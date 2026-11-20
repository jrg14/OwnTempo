from rest_framework.permissions import BasePermission

from .models import Membership


def _space_id(view):
    return view.kwargs.get("space_id") or view.kwargs.get("pk")


class IsSpaceMember(BasePermission):
    message = "No perteneces a este espacio."

    def has_permission(self, request, view):
        return Membership.objects.filter(
            space_id=_space_id(view),
            user=request.user,
        ).exists()

    def has_object_permission(self, request, view, obj):
        space_id = getattr(obj, "space_id", None) or obj.id
        return Membership.objects.filter(
            space_id=space_id,
            user=request.user,
        ).exists()


class IsSpaceOwner(BasePermission):
    message = "Solo el propietario puede realizar esta acción."

    def has_permission(self, request, view):
        return Membership.objects.filter(
            space_id=_space_id(view),
            user=request.user,
            role=Membership.Role.OWNER,
        ).exists()

    def has_object_permission(self, request, view, obj):
        space_id = getattr(obj, "space_id", None) or obj.id
        return Membership.objects.filter(
            space_id=space_id,
            user=request.user,
            role=Membership.Role.OWNER,
        ).exists()
