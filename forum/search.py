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
    return (
        Thread.objects.filter(is_deleted=False, merged_into__isnull=True)
        .select_related("author")
        .annotate(
            puntuacion=Coalesce(Subquery(votos, output_field=IntegerField()), 0),
            num_respuestas=Coalesce(Subquery(respuestas, output_field=IntegerField()), 0),
        )
    )


def buscar_hilos(texto="", autor="", desde=None, hasta=None, min_votos=None, orden="recientes"):
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

    if orden == "votos":
        return consulta.order_by("-puntuacion", "-created_at")
    return consulta.order_by("-created_at")


def feed_nuevos():
    return hilos_visibles().order_by("-created_at")


def feed_populares():
    return hilos_visibles().order_by("-puntuacion", "-num_respuestas", "-created_at")


def feed_sin_respuesta():
    return hilos_visibles().filter(num_respuestas=0).order_by("-created_at")