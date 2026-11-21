from django.db import transaction

from .models import CalendarEvent


def _normalize_mode(validated_data):
    if validated_data["all_day"]:
        validated_data["start_at"] = None
        validated_data["end_at"] = None
    else:
        validated_data["date"] = None
    return validated_data


@transaction.atomic
def create_event(user, space, validated_data):
    data = _normalize_mode(dict(validated_data))
    event = CalendarEvent(space=space, created_by=user, **data)
    event.save()
    return event


@transaction.atomic
def update_event(event, validated_data):
    event = CalendarEvent.objects.select_for_update().get(pk=event.pk)
    data = {
        "title": event.title,
        "description": event.description,
        "start_at": event.start_at,
        "end_at": event.end_at,
        "all_day": event.all_day,
        "date": event.date,
        "location": event.location,
        "color": event.color,
        **validated_data,
    }
    data = _normalize_mode(data)
    for field, value in data.items():
        setattr(event, field, value)
    event.save()
    return event
