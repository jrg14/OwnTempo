from django.db import transaction
from django.utils import timezone

from .models import WishItem


def _apply_status(wish, status):
    wish.status = status
    if status == WishItem.Status.OBTAINED:
        wish.obtained_at = wish.obtained_at or timezone.now()
    else:
        wish.obtained_at = None


@transaction.atomic
def create_wish(user, space, validated_data):
    status = validated_data.pop("status", WishItem.Status.PENDING)
    wish = WishItem(space=space, created_by=user, **validated_data)
    _apply_status(wish, status)
    wish.save()
    return wish


@transaction.atomic
def update_wish(wish, validated_data):
    wish = WishItem.objects.select_for_update().get(pk=wish.pk)
    status = validated_data.pop("status", None)
    for field, value in validated_data.items():
        setattr(wish, field, value)
    if status is not None:
        _apply_status(wish, status)
    wish.save()
    return wish
