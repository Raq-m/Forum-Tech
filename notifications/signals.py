from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse

from chat.models import Message

from .models import NotificationType
from .tasks import create_notification_async


@receiver(post_save, sender=Message)
def notify_new_chat_message(sender, instance, created, **kwargs):
    if not created:
        return

    conv = instance.conversation

    if instance.sender_id == conv.initiator_id:
        recipient_id = conv.recipient_id
    else:
        recipient_id = conv.initiator_id

    create_notification_async.delay(
        recipient_id=recipient_id,
        notification_type=NotificationType.NEW_MESSAGE,
        title="Nuevo mensaje privado",
        body=f"{instance.sender.username}: {instance.text[:50]}",
        link=reverse("chat:detail", args=[conv.pk]),
    )