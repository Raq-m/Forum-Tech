from django.db.models import Count, Exists, IntegerField, OuterRef, Q, Subquery, Sum
from django.db.models.functions import Coalesce

from .models import Reply, Thread, ThreadVote


def hilos_visibles():
    """Hilos que pueden salir en listados, búsquedas y feeds."""

    votos = (
        ThreadVote.objects.filter(thread=OuterRef("pk"))
        .order_by()
        .values("thread")
        .annotate(total=Sum("value"))
        .values("total")
    )
    respuestas = (
        Reply.objects.filter(thread=OuterRef("pk"), is_deleted=False)
        .order_by()
        .values("thread")
        .annotate(total=Count("pk"))
        .values("total")
    )

    solucion_visible = Reply.objects.filter(
        pk=OuterRef("accepted_reply_id"), is_deleted=False
    )
    return (
        Thread.objects.filter(is_deleted=False, merged_into__isnull=True)
        .select_related("author")
        .annotate(
            puntuacion=Coalesce(Subquery(votos, output_field=IntegerField()), 0),
            num_respuestas=Coalesce(Subquery(respuestas, output_field=IntegerField()), 0),
            esta_resuelto=Exists(solucion_visible),
        )
    )


def buscar_hilos(
    texto="", autor="", desde=None, hasta=None, min_votos=None,
    etiquetas=None, resuelto=None, orden="recientes",
):
    consulta = hilos_visibles()


    for palabra in (texto or "").split():
        respuesta_coincide = Reply.objects.filter(
            thread=OuterRef("pk"), is_deleted=False, content__icontains=palabra
        )
        consulta = consulta.filter(
            Q(title__icontains=palabra)
            | Q(content__icontains=palabra)
            | Exists(respuesta_coincide)
        )

    if autor:
        consulta = consulta.filter(author__username__iexact=autor)
    if desde:
        consulta = consulta.filter(created_at__date__gte=desde)
    if hasta:
        consulta = consulta.filter(created_at__date__lte=hasta)
    if min_votos is not None:
        consulta = consulta.filter(puntuacion__gte=min_votos)
    for nombre in etiquetas or []:
        consulta = consulta.filter(tags__name=nombre.strip().lstrip("#").lower())
    if resuelto is not None:
        consulta = consulta.filter(esta_resuelto=resuelto)

    if orden == "votos":
        return consulta.order_by("-puntuacion", "-created_at")
    return consulta.order_by("-created_at")


def feed_nuevos():
    return hilos_visibles().order_by("-created_at")


def feed_populares():
    return hilos_visibles().order_by("-puntuacion", "-num_respuestas", "-created_at")


def feed_sin_respuesta():
    return hilos_visibles().filter(num_respuestas=0).order_by("-created_at")


def feed_siguiendo(usuario):
    """Hilos escritos por los usuarios que `usuario` sigue."""
    return (
        hilos_visibles()
        .filter(author__follows_received__follower=usuario)
        .order_by("-created_at")
    )