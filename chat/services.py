from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Q

from .models import Conversation, Message

User = get_user_model()


@transaction.atomic
def get_or_create_conversation(user, other_user_id):
    """
    Busca la conversación entre dos usuarios; si no existe, la crea.
    """
    try:
        other_user = User.objects.get(pk=other_user_id)
    except User.DoesNotExist:
        raise ValidationError("El usuario no existe.")

    if other_user == user:
        raise ValidationError("No puedes iniciar una conversación contigo mismo.")

    conversation = Conversation.objects.filter(
        Q(initiator=user, recipient=other_user)
        | Q(initiator=other_user, recipient=user)
    ).first()

    if conversation is None:
        conversation = Conversation.objects.create(
            initiator=user,
            recipient=other_user,
        )

    return conversation


@transaction.atomic
def send_message(user, conversation_id, text):
    """
    Envía un mensaje comprobando que quien lo envía participa en la conversación.
    """
    clean_text = text.strip()
    if not clean_text:
        raise ValidationError("El mensaje no puede estar vacío.")

    conversation = Conversation.objects.select_for_update().get(pk=conversation_id)

    if user != conversation.initiator and user != conversation.recipient:
        raise PermissionDenied("No tienes permiso para escribir en esta conversación.")

    message = Message.objects.create(
        conversation=conversation,
        sender=user,
        text=clean_text,
    )


    conversation.save(update_fields=["updated_at"])

    return message


@transaction.atomic
def mark_messages_as_read(conversation_id, user):
    """
    Marca como leídos los mensajes que te han enviado los demás.
    """
    conversation = Conversation.objects.get(pk=conversation_id)

    if user != conversation.initiator and user != conversation.recipient:
        raise PermissionDenied("No tienes acceso a esta conversación.")

    Message.objects.filter(
        conversation=conversation,
        is_read=False,
    ).exclude(sender=user).update(is_read=True)