# Notificaciones de chat (parte 11)

Cuando un usuario recibe un mensaje privado, se le crea un aviso. Se hace en segundo plano con Celery y Redis, para que la página no espere.

## Cómo funciona

1. Se guarda un mensaje nuevo en `chat.Message`.
2. Una señal de Django (`notifications/signals.py`) lo detecta.
3. La señal pide a Celery crear la notificación (`create_notification_async`).
4. Esa tarea guarda la `Notification` y pide otra tarea que simula el envío de un correo (`send_notification_email_async`, solo escribe en el log).

La app `notifications` es independiente de `forum.Notification` (respuestas, menciones y votos). Por eso su campo `recipient` usa `related_name="chat_notifications"`.

## Puesta en marcha

1. En el `.env`, poner (el `.env.example` ya lo trae):

   ```
   REDIS_URL=redis://localhost:6379/0
   ```

   Si la variable existe pero está vacía, Celery no encuentra el broker.

2. Arrancar Redis con Docker (Docker Desktop abierto):

   ```bash
   docker run -d --name redis-forum -p 6379:6379 redis
   ```

   Las siguientes veces: `docker start redis-forum`.

3. Arrancar el worker de Celery. En Windows hace falta `--pool=solo`:

   ```bash
   celery -A config worker --loglevel=info --pool=solo
   ```

4. Arrancar el servidor:

   ```bash
   python manage.py runserver
   ```

Hay que reiniciar el worker cada vez que se cambie código de `notifications/`.

## Probar

Con todo encendido, enviar un mensaje desde `/chat/nuevo/<id del usuario>/`. En la terminal de Celery aparecen `create_notification_async ... succeeded` y `Enviando correo a ...`.

## Tests

```bash
python manage.py test notifications
```

En los tests las tareas se ejecutan al momento (`task_always_eager`), sin Redis.

## Pendiente

- Pantalla para ver las notificaciones y marcarlas como leídas.
- Enviar correos reales (ahora solo se escribe en el log).
- Unificar con `forum.Notification` si el equipo lo decide.