from django.db.models.signals import post_delete
from django.dispatch import receiver

from apps.spaces.models import Membership

from .models import TaskAssignment


@receiver(post_delete, sender=Membership)
def remove_departed_member_assignments(sender, instance, **kwargs):
    TaskAssignment.objects.filter(
        task__space_id=instance.space_id,
        user_id=instance.user_id,
    ).delete()
