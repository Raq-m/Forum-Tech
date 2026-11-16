import logging

from celery import shared_task
from django.contrib.auth import get_user_model

from .models import Notification

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task
def send_notification_email_async(user_id, subject, message_body):
    """Simula enviar un correo en segundo plano (solo escribe en el log)."""
    try:
        user = User.objects.get(pk=user_id)
        logger.info("Enviando correo a %s | Asunto: %s", user.email, subject)
        return f"Email procesado para usuario {user_id}"
    except User.DoesNotExist:
        logger.error("Usuario %s no encontrado.", user_id)
        return "Usuario inexistente"


@shared_task
def create_notification_async(recipient_id, notification_type, title, body, link=""):
    """Crea el aviso dentro de la web y pide el correo en otra tarea."""
    try:
        recipient = User.objects.get(pk=recipient_id)
    except User.DoesNotExist:
        return "Destinatario no encontrado."

    notification = Notification.objects.create(
        recipient=recipient,
        notification_type=notification_type,
        title=title,
        body=body,
        link=link,
    )
    send_notification_email_async.delay(
        recipient_id,
        subject=f"Forum Tech: {title}",
        message_body=body,
    )
    return f"Notificación #{notification.pk} registrada."