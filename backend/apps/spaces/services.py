from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from .models import Invitation, Membership, Space


class SpaceOperationError(Exception):
    pass


@transaction.atomic
def ensure_personal_space(user):
    space, _created = Space.objects.get_or_create(
        created_by=user,
        kind=Space.Kind.PERSONAL,
        defaults={"name": "Mi espacio"},
    )
    Membership.objects.get_or_create(
        user=user,
        space=space,
        defaults={"role": Membership.Role.OWNER},
    )
    return space


@transaction.atomic
def create_shared_space(user, name):
    space = Space.objects.create(
        name=name,
        kind=Space.Kind.SHARED,
        created_by=user,
    )
    Membership.objects.create(
        user=user,
        space=space,
        role=Membership.Role.OWNER,
    )
    return space


def _require_owner(space, user):
    if not Membership.objects.filter(
        space=space,
        user=user,
        role=Membership.Role.OWNER,
    ).exists():
        raise SpaceOperationError("Solo el propietario puede realizar esta acción.")


@transaction.atomic
def invite_user(space, invited_by, username):
    space = Space.objects.select_for_update().get(pk=space.pk)
    _require_owner(space, invited_by)

    if space.kind != Space.Kind.SHARED:
        raise SpaceOperationError("El espacio personal no admite invitaciones.")

    invited_user = get_user_model().objects.filter(username=username).first()
    if invited_user is None:
        raise SpaceOperationError("No existe ningún usuario con ese nombre.")

    if Membership.objects.filter(space=space, user=invited_user).exists():
        raise SpaceOperationError("El usuario ya pertenece a este espacio.")

    if Invitation.objects.filter(
        space=space,
        invited_user=invited_user,
        status=Invitation.Status.PENDING,
    ).exists():
        raise SpaceOperationError("El usuario ya tiene una invitación pendiente.")

    return Invitation.objects.create(
        space=space,
        invited_user=invited_user,
        invited_by=invited_by,
    )


@transaction.atomic
def respond_to_invitation(invitation, user, accepted):
    invitation = Invitation.objects.select_for_update().get(pk=invitation.pk)

    if invitation.invited_user_id != user.id:
        raise SpaceOperationError("Esta invitación pertenece a otro usuario.")

    if invitation.status != Invitation.Status.PENDING:
        raise SpaceOperationError("La invitación ya no está pendiente.")

    if accepted:
        Membership.objects.get_or_create(
            user=user,
            space=invitation.space,
            defaults={"role": Membership.Role.MEMBER},
        )
        invitation.status = Invitation.Status.ACCEPTED
    else:
        invitation.status = Invitation.Status.REJECTED

    invitation.responded_at = timezone.now()
    invitation.save(update_fields=("status", "responded_at"))
    return invitation


@transaction.atomic
def cancel_invitation(invitation, user):
    invitation = Invitation.objects.select_for_update().select_related("space").get(
        pk=invitation.pk
    )
    _require_owner(invitation.space, user)

    if invitation.status != Invitation.Status.PENDING:
        raise SpaceOperationError("La invitación ya no está pendiente.")

    invitation.status = Invitation.Status.CANCELLED
    invitation.responded_at = timezone.now()
    invitation.save(update_fields=("status", "responded_at"))
    return invitation


@transaction.atomic
def leave_shared_space(space, user):
    membership = Membership.objects.select_for_update().filter(
        space=space,
        user=user,
    ).first()
    if membership is None:
        raise SpaceOperationError("No perteneces a este espacio.")
    if space.kind != Space.Kind.SHARED:
        raise SpaceOperationError("No puedes abandonar tu espacio personal.")
    if membership.role == Membership.Role.OWNER:
        raise SpaceOperationError("El propietario no puede abandonar el espacio.")

    membership.delete()


@transaction.atomic
def remove_member(space, requested_by, user_id):
    _require_owner(space, requested_by)
    membership = Membership.objects.select_for_update().filter(
        space=space,
        user_id=user_id,
    ).first()
    if membership is None:
        raise SpaceOperationError("El usuario no pertenece a este espacio.")
    if membership.role == Membership.Role.OWNER:
        raise SpaceOperationError("No se puede retirar al propietario.")

    membership.delete()
