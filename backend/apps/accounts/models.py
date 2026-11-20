from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """OwnTempo user identified only by a username."""

    email = None
    REQUIRED_FIELDS = []
