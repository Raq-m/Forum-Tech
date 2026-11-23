
"""Configuración PostgreSQL para Forum-Tech."""

import os
from urllib.parse import urlparse, parse_qs, unquote

from django.core.exceptions import ImproperlyConfigured


def database_config():
    """
    Obtiene la configuración de PostgreSQL.
    Admite DATABASE_URL (Neon) y variables POSTGRES_*.
    """

    database_url = os.getenv("DATABASE_URL")

    if database_url:
        parsed = urlparse(database_url)

        if parsed.scheme not in ("postgres", "postgresql"):
            raise ImproperlyConfigured(
                "DATABASE_URL debe ser una URL de PostgreSQL."
            )

        if not parsed.hostname or not parsed.path:
            raise ImproperlyConfigured(
                "DATABASE_URL no contiene los datos necesarios."
            )

        query = parse_qs(parsed.query)

        config = {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": unquote(parsed.path.lstrip("/")),
            "USER": unquote(parsed.username or ""),
            "PASSWORD": unquote(parsed.password or ""),
            "HOST": parsed.hostname,
            "PORT": str(parsed.port or 5432),
            "CONN_MAX_AGE": 60,
            "OPTIONS": {
                "sslmode": query.get("sslmode", ["require"])[0],
            },
        }

        return config

    # Alternativa mediante variables individuales
    required = (
        "POSTGRES_DB",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
        "POSTGRES_HOST",
    )

    missing = [
        name for name in required
        if not os.getenv(name)
    ]

    if missing:
        raise ImproperlyConfigured(
            "Faltan variables PostgreSQL: " + ", ".join(missing)
        )

    return {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ["POSTGRES_DB"],
        "USER": os.environ["POSTGRES_USER"],
        "PASSWORD": os.environ["POSTGRES_PASSWORD"],
        "HOST": os.environ["POSTGRES_HOST"],
        "PORT": os.getenv("POSTGRES_PORT", "5432"),
        "CONN_MAX_AGE": 60,
        "OPTIONS": {
            "sslmode": "require",
        },
    }
