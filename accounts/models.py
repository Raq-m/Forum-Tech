from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    city = models.CharField(max_length=100, blank=True)
    bio = models.TextField(blank=True)
    avatar = models.ImageField(
        upload_to="avatars/",
        blank=True,
        null=True,
    )
    suspended_until = models.DateTimeField(
        null=True,
        blank=True,
    )

    @property
    def is_suspended(self):
        return (
            self.suspended_until is not None
            and self.suspended_until > timezone.now()
        )

    def __str__(self):
        return self.username
    