
"""Configuración de producción para Forum-Tech."""

import os

from django.core.exceptions import ImproperlyConfigured

from .base import *
from .postgresql import database_config


# ==================================================
# SEGURIDAD
# ==================================================

DEBUG = False

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ImproperlyConfigured("Define SECRET_KEY en las variables de entorno.")


def _lista(nombre):
    return [
        valor.strip()
        for valor in os.getenv(nombre, "").split(",")
        if valor.strip()
    ]


ALLOWED_HOSTS = _lista("ALLOWED_HOSTS")

if not ALLOWED_HOSTS:
    raise ImproperlyConfigured(
        "Define ALLOWED_HOSTS en las variables de entorno."
    )

CSRF_TRUSTED_ORIGINS = _lista("CSRF_TRUSTED_ORIGINS")


# ==================================================
# BASE DE DATOS POSTGRESQL (NEON)
# ==================================================

DATABASES = {
    "default": database_config()
}


# ==================================================
# ARCHIVOS ESTÁTICOS
# ==================================================

STATIC_ROOT = BASE_DIR / "staticfiles"


# ==================================================
# REDIS Y DJANGO CHANNELS
# ==================================================

REDIS_URL = os.getenv("REDIS_URL")

if not REDIS_URL:
    raise ImproperlyConfigured(
        "Define REDIS_URL en las variables de entorno."
    )

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [REDIS_URL],
        },
    },
}


# ==================================================
# SEGURIDAD HTTPS
# ==================================================

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

SECURE_SSL_REDIRECT = True
