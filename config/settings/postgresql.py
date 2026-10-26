"""Configuración compartida de PostgreSQL para desarrollo y pruebas reales."""
import os

from django.core.exceptions import ImproperlyConfigured


def database_config():
    required = ("POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD")
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        raise ImproperlyConfigured("Define en .env: " + ", ".join(missing))
    return {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ["POSTGRES_DB"],
        "USER": os.environ["POSTGRES_USER"],
        "PASSWORD": os.environ["POSTGRES_PASSWORD"],
        "HOST": os.getenv("POSTGRES_HOST", "127.0.0.1"),
        "PORT": os.getenv("POSTGRES_PORT", "5432"),
    }
