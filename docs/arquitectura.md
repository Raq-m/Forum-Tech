# Arquitectura técnica (módulo 6)

El apartado 6 del documento del proyecto describe una arquitectura recomendada. El proyecto usa Python con Django, que el documento admite. Según la guía de integración, la recomendación de otro framework no implica reescribir nada.

## Recomendaciones del documento y estado

| Recomendación | Estado en el proyecto |
|---|---|
| Frontend con renderizado en servidor (Next.js o Nuxt) para SEO | Django genera el HTML en el servidor con plantillas, así que hilos y respuestas llegan completos a los buscadores. No se usa Next.js ni Nuxt |
| Backend en Node, Python o Go | Python con Django 5.2, y Channels con Daphne para WebSockets |
| PostgreSQL | Desarrollo usa PostgreSQL local desde la sesión 7. SQLite sigue disponible para pruebas rápidas. Falta que el equipo confirme el motor de producción |
| Redis para colas de notificaciones y WebSockets | Hecho para producción: `config/settings/production.py` usa `channels_redis` y exige `REDIS_URL`. En desarrollo la capa de canales va en memoria |
| Redis para sesiones y caché de hilos populares | No implementado |
| Meilisearch o Elasticsearch | No implementado: la búsqueda consulta la base de datos |
| Cloudflare R2 o AWS S3 para avatares y multimedia | No implementado: las imágenes del editor se guardan en `media/` |

## API REST (sesión 8)

La app `api` ofrece `/api/v1/` con hilos, etiquetas y votos propios privados.
Comparte usuarios, ORM y PostgreSQL con la web HTML. El archivo lógico y los
votos de hilos usan servicios del foro. La autenticación utiliza sesiones Django
con CSRF; las escrituras exigen cuenta no suspendida y la edición de hilos exige
autoría. Swagger está en `/api/docs/`; véase [sesion_8.md](sesion_8.md).

## Configuración de producción

Se usa `config.settings.production`. Necesita estas variables de entorno (ver `.env.example`) y se niega a arrancar si faltan:

- `ALLOWED_HOSTS`: dominios del sitio, separados por comas. También valida el origen de las conexiones WebSocket (`config/asgi.py`)
- `CSRF_TRUSTED_ORIGINS`: orígenes con `https://` para que los formularios funcionen tras un dominio
- `REDIS_URL`: dirección de Redis para la capa de canales. Con varios procesos, la capa en memoria no comunica entre ellos

No hay que copiar a producción las opciones de `development.py` (por ejemplo `DEBUG = True` ni la capa de canales en memoria). Cada persona necesita su propio `.env`, que no se sube a Git.

## Cómo comprobarlo

```
python manage.py check --settings=config.settings.production
```

Sin las variables debe fallar con un mensaje claro. Con ellas:

```
ALLOWED_HOSTS=ejemplo.com CSRF_TRUSTED_ORIGINS=https://ejemplo.com REDIS_URL=redis://localhost:6379/0 python manage.py check --settings=config.settings.production
```

## Pendiente

| Qué falta | Quién lo decide |
|---|---|
| Elegir el motor de base de datos de producción (SQLite o PostgreSQL) y configurarlo | Equipo |
| Búsqueda de texto completo con ranking y tolerancia a erratas | Depende de PostgreSQL o de un buscador externo |
| Antes de publicar, resolver las 4 advertencias de `check --deploy`: `SECURE_HSTS_SECONDS`, `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE` y `CSRF_COOKIE_SECURE`. Solo activarlas cuando el sitio se sirva por HTTPS; HSTS es difícil de revertir | Módulo 6 |
| Probar las notificaciones en tiempo real con un Redis real | Módulos 4 y 6 |
| Sesiones y caché en Redis, buscador externo y almacenamiento S3 o R2 | Mejoras opcionales, al final |
