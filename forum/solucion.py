from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from .models import Reply, Thread


@transaction.atomic
def aceptar_solucion(hilo, respuesta, usuario):
    """Relee el estado bajo bloqueo, también si el objeto recibido está obsoleto."""
    actual = Thread.objects.select_for_update().get(pk=hilo.pk)
    if usuario.is_suspended or usuario.pk != actual.author_id:
        raise PermissionDenied("Solo el autor del hilo puede aceptar una solución.")
    if actual.is_deleted or actual.merged_into_id:
        raise ValidationError("El hilo ya no está disponible.")
    if not Reply.objects.filter(
        pk=respuesta.pk, thread=actual, is_deleted=False
    ).exists():
        raise ValidationError("La respuesta no es válida para este hilo.")
    Thread.objects.filter(pk=actual.pk).update(accepted_reply=respuesta)
    hilo.accepted_reply = respuesta
