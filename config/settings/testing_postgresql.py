"""Pruebas de integridad y bloqueos sobre PostgreSQL (usuario con CREATEDB)."""
from .testing import *
from .postgresql import database_config
import os

# unittest descubre también este módulo por su nombre testing_*. No exigir
# credenciales PostgreSQL cuando se importa durante una suite de SQLite.
if os.environ.get("DJANGO_SETTINGS_MODULE") == __name__:
    DATABASES = {"default": database_config()}
