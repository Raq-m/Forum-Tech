# Forum Tech

Foro tecnológico desarrollado con Python 3.12, Django 5.2 y PostgreSQL.
Incluye usuarios, perfiles, hilos, respuestas, etiquetas, votos, soluciones,
seguimiento, búsquedas, moderación y notificaciones.

## Sesión 7

La sesión está implementada y explicada paso a paso en
[docs/sesion_7.md](docs/sesion_7.md). Incluye la adaptación de los ejemplos de
Tech2Hand a Forum Tech, PostgreSQL local, integridad, índices, ORM, transacciones,
pruebas concurrentes, EXPLAIN y copias de seguridad.

## Revisión del profesor: sesiones 7 y 8

Las dos sesiones están adaptadas al dominio del foro. La sesión 7 incorpora
PostgreSQL, restricciones, estadísticas y transacciones; la sesión 8 añade la
API REST de hilos, etiquetas y votos, con permisos y documentación OpenAPI.

Para preparar una copia nueva con Python 3.12:

```bash
git clone https://github.com/malena1688/Forum-Tech.git
cd Forum-Tech
# Si se revisa una pull request, selecciona su rama antes de continuar.
python3.12 -m venv .venv312
source .venv312/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Completa `SECRET_KEY` en tu `.env`. Para una comprobación rápida con SQLite:

```bash
python manage.py test --settings=config.settings.testing --noinput
```

Resultado verificado: 123 pruebas descubiertas, 122 correctas y una omitida
porque necesita bloqueos reales de PostgreSQL. Para la comprobación completa,
crea tu base y rol PostgreSQL y configura `.env` siguiendo
[docs/sesion_7.md](docs/sesion_7.md), apartados 3 y 14. La suite PostgreSQL pasa
las 123 pruebas, incluida la prueba concurrente.

Para explorar la web y API sin configurar PostgreSQL todavía:

```bash
DB_ENGINE=sqlite python manage.py migrate
DB_ENGINE=sqlite python manage.py datos_demo
DB_ENGINE=sqlite python manage.py runserver
```

Las cuentas de demostración y los pasos de revisión manual están documentados
en [sesion_7.md](docs/sesion_7.md) y [sesion_8.md](docs/sesion_8.md).
Las cuentas y datos locales del desarrollador no se incluyen en el repositorio.

## Arranque en este equipo

```bash
source .venv312/bin/activate
/opt/homebrew/bin/pg_ctl -D "$PWD/.local/postgresql" status
# Si está detenido:
/opt/homebrew/bin/pg_ctl -D "$PWD/.local/postgresql" \
  -l "$PWD/.local/postgresql.log" \
  -o '-p 55432 -k /tmp -h 127.0.0.1' start
python manage.py runserver
```

Abre http://127.0.0.1:8000/forum/threads/.
Para instalar en otro equipo sigue el apartado 3 de la guía.

## Comprobaciones
La sesión 8 incorpora una API REST adaptada a los hilos, etiquetas y votos.
Consulta [docs/sesion_8.md](docs/sesion_8.md) para probarla con tu cuenta.
Con el servidor arrancado:

- API: http://127.0.0.1:8000/api/v1/threads/
- Swagger: http://127.0.0.1:8000/api/docs/
- Login de API: http://127.0.0.1:8000/api/auth/login/


```bash
python manage.py check
python manage.py test --settings=config.settings.testing_postgresql --noinput
python manage.py test --settings=config.settings.testing --noinput
python manage.py analizar_foro
```

La base local y sus credenciales están en `.local/` y `.env`, excluidos de Git.
SQLite sigue disponible con `DB_ENGINE=sqlite`; las pruebas rápidas lo seleccionan
mediante `config.settings.testing`.
