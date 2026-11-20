from django.contrib.auth.models import AbstractUser

from .managers import UserManager


class User(AbstractUser):
    """OwnTempo user identified only by a username."""

    email = None
    REQUIRED_FIELDS = []

    objects = UserManager()
