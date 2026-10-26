from .base import *

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "[::1]"]

INSTALLED_APPS = [
    "daphne",
    *INSTALLED_APPS,
]

ASGI_APPLICATION = "config.asgi.application"

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    },
}
# SQLite sigue disponible con DB_ENGINE=sqlite para comparar ambos motores.
if os.getenv("DB_ENGINE", "postgresql") == "postgresql":
    from .postgresql import database_config
    DATABASES = {"default": database_config()}
