from django.core.exceptions import PermissionDenied, ValidationError

from .models import Thread


def aceptar_solucion(hilo, respuesta, usuario):
    """Marca una respuesta como solución. Solo puede el autor del hilo."""
    suspendido = getattr(usuario, "is_suspended", False)
    if callable(suspendido):
        suspendido = suspendido()
    if suspendido or usuario.pk != hilo.author_id:
        raise PermissionDenied("Solo el autor del hilo puede aceptar una solución.")
    if respuesta.thread_id != hilo.pk or respuesta.is_deleted:
        raise ValidationError("La respuesta no es válida para este hilo.")
    Thread.objects.filter(pk=hilo.pk).update(accepted_reply=respuesta)
    hilo.accepted_reply = respuesta

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["follower", "followed"],
                name="unique_follow_per_pair",
            ),
            models.CheckConstraint(
                condition=~models.Q(follower=models.F("followed")),
                name="cannot_follow_yourself",
            ),
        ]

    def __str__(self):
        return f"{self.follower} sigue a {self.followed}"