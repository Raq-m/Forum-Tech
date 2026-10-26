from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from .models import Notification, Reply, Thread, ThreadVote


@transaction.atomic
def record_thread_vote(thread, user, value):
    """Voto compartido por web y API; 0 retira la fila existente."""
    if not user.is_authenticated or user.is_suspended:
        raise PermissionDenied("Necesitas una cuenta activa para votar.")
    if value not in (-1, 0, 1):
        raise ValidationError("El valor debe ser 1, -1 o 0.")
    current = Thread.objects.select_for_update().get(pk=thread.pk)
    if current.is_deleted or current.merged_into_id:
        raise ValidationError("El hilo ya no está disponible.")
    lookup = {"thread": current, "user": user}
    if value == 0:
        ThreadVote.objects.filter(**lookup).delete()
    else:
        ThreadVote.objects.update_or_create(**lookup, defaults={"value": value})
    return {"score": current.votes.aggregate(total=Sum("value"))["total"] or 0, "user_vote": value}


@transaction.atomic
def merge_threads(source_id, target_id):
    if source_id == target_id:
        raise ValidationError(
            "No puedes fusionar un hilo consigo mismo."
        )

    threads = {
        thread.pk: thread
        for thread in (
            Thread.objects
            .select_for_update()
            .filter(pk__in=[source_id, target_id])
            .order_by("pk")
        )
    }

    if len(threads) != 2:
        raise ValidationError(
            "No se encuentran los dos hilos."
        )

    source = threads[source_id]
    target = threads[target_id]

    if source.is_deleted or target.is_deleted:
        raise ValidationError(
            "No se pueden fusionar hilos eliminados."
        )

    if source.merged_into_id or target.merged_into_id:
        raise ValidationError(
            "Selecciona hilos que no esten ya fusionados."
        )

    if target.is_locked:
        raise ValidationError(
            "El hilo de destino esta bloqueado."
        )

    # Actualizar los enlaces de avisos sobre respuestas que se moveran.
    Notification.objects.filter(
        reply__thread_id=source.pk,
    ).update(thread_id=target.pk)

    # Mantener los identificadores de las respuestas y sus votos.
    moved = Reply.objects.filter(
        thread_id=source.pk,
    ).update(thread_id=target.pk)

    # Evitar cadenas en enlaces de fusiones anteriores.
    Thread.objects.filter(
        merged_into_id=source.pk,
    ).update(
        merged_into_id=target.pk,
        updated_at=timezone.now(),
    )

    # La solución del origen deja de pertenecer al hilo tras mover respuestas.
    source.accepted_reply = None
    source.merged_into = target
    source.is_locked = True
    source.save(
        update_fields=[
            "accepted_reply",
            "merged_into",
            "is_locked",
            "updated_at",
        ],
    )

    return moved

@transaction.atomic
def archive_thread(thread_id, user):
    """Ejercicio 4: el autor archiva su hilo una sola vez, bajo bloqueo."""
    thread = Thread.objects.select_for_update().get(pk=thread_id)
    if not user.is_authenticated or user.pk != thread.author_id or user.is_suspended:
        raise PermissionDenied("Solo el autor activo puede archivar su hilo.")
    if thread.is_deleted or thread.merged_into_id:
        raise ValidationError("El hilo ya no está disponible.")
    thread.is_deleted = True
    thread.save(update_fields=["is_deleted", "updated_at"])
    return thread
