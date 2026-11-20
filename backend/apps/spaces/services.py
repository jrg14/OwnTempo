from django.db import transaction

from .models import Membership, Space


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
