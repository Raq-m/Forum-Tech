from .base import *

DEBUG = False

import os

from django.core.exceptions import ImproperlyConfigured


def _lista(nombre):
    """Lee una variable de entorno con valores separados por comas."""
    return [v.strip() for v in os.getenv(nombre, "").split(",") if v.strip()]



ALLOWED_HOSTS = _lista("ALLOWED_HOSTS")
if not ALLOWED_HOSTS:
    raise ImproperlyConfigured("Define ALLOWED_HOSTS (separados por comas) en producción.")


CSRF_TRUSTED_ORIGINS = _lista("CSRF_TRUSTED_ORIGINS")


REDIS_URL = os.getenv("REDIS_URL")
if not REDIS_URL:
    raise ImproperlyConfigured("Define REDIS_URL en producción (capa de canales).")

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [REDIS_URL]},
    },
}