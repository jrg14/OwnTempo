from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .services import ensure_personal_space


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_personal_space_for_new_user(sender, instance, created, **kwargs):
    if created:
        ensure_personal_space(instance)
