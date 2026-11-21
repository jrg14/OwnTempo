from django.db import transaction
from django.db.models import F, Max
from django.utils import timezone

from .models import ShoppingItem, ShoppingList


class ShoppingOperationError(Exception):
    pass


@transaction.atomic
def create_shopping_list(user, space, validated_data):
    shopping_list = ShoppingList(space=space, created_by=user, **validated_data)
    shopping_list.save()
    return shopping_list


@transaction.atomic
def update_shopping_list(shopping_list, validated_data):
    shopping_list = ShoppingList.objects.select_for_update().get(pk=shopping_list.pk)
    for field, value in validated_data.items():
        setattr(shopping_list, field, value)
    shopping_list.save()
    return shopping_list


def _apply_status(item, status):
    item.status = status
    if status == ShoppingItem.Status.PURCHASED:
        item.purchased_at = item.purchased_at or timezone.now()
    else:
        item.purchased_at = None


@transaction.atomic
def create_shopping_item(user, shopping_list, validated_data):
    status = validated_data.pop("status", ShoppingItem.Status.PENDING)
    shopping_list = ShoppingList.objects.select_for_update().get(pk=shopping_list.pk)
    current_max = (
        ShoppingItem.objects.filter(shopping_list=shopping_list)
        .aggregate(value=Max("position"))["value"]
    )
    item = ShoppingItem(
        shopping_list=shopping_list,
        created_by=user,
        position=0 if current_max is None else current_max + 1,
        **validated_data,
    )
    _apply_status(item, status)
    item.save()
    ShoppingList.objects.filter(pk=shopping_list.pk).update(updated_at=timezone.now())
    return item


@transaction.atomic
def update_shopping_item(item, validated_data):
    item = ShoppingItem.objects.select_for_update().select_related(
        "shopping_list"
    ).get(pk=item.pk)
    status = validated_data.pop("status", None)
    for field, value in validated_data.items():
        setattr(item, field, value)
    if status is not None:
        _apply_status(item, status)
    item.save()
    ShoppingList.objects.filter(pk=item.shopping_list_id).update(
        updated_at=timezone.now()
    )
    return item


@transaction.atomic
def reorder_shopping_items(shopping_list, item_ids):
    requested_ids = list(item_ids)
    if len(requested_ids) != len(set(requested_ids)):
        raise ShoppingOperationError("La reordenación contiene productos duplicados.")

    items = list(
        ShoppingItem.objects.select_for_update()
        .filter(shopping_list=shopping_list)
        .order_by("position", "id")
    )
    existing_ids = {item.id for item in items}
    if set(requested_ids) != existing_ids:
        raise ShoppingOperationError(
            "La reordenación debe incluir exactamente todos los productos de la lista."
        )

    if not items:
        return []

    offset = max(item.position for item in items) + len(items) + 1
    ShoppingItem.objects.filter(shopping_list=shopping_list).update(
        position=F("position") + offset
    )
    items_by_id = {item.id: item for item in items}
    for position, item_id in enumerate(requested_ids):
        item = items_by_id[item_id]
        item.position = position
        item.save(update_fields=("position", "updated_at"))

    ShoppingList.objects.filter(pk=shopping_list.pk).update(updated_at=timezone.now())
    return [items_by_id[item_id] for item_id in requested_ids]
