from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .models import Notification, Reply, Thread


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

    source.merged_into = target
    source.is_locked = True
    source.save(
        update_fields=[
            "merged_into",
            "is_locked",
            "updated_at",
        ],
    )

    return moved