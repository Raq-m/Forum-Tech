"""Consultas de la sesión 7, adaptadas de productos a hilos y etiquetas."""
from django.db.models import Avg, Count, Max, Min, Q

from .models import Tag
from .search import hilos_visibles


def resumen_foro():
    return hilos_visibles().aggregate(
        total=Count("pk"),
        media_respuestas=Avg("num_respuestas"),
        minimo_visitas=Min("views_count"),
        maximo_visitas=Max("views_count"),
    )


def etiquetas_populares():
    # Ejercicio 1: cinco etiquetas con más hilos visibles.
    return Tag.objects.annotate(
        num_hilos=Count("threads", filter=Q(
            threads__is_deleted=False, threads__merged_into__isnull=True
        )),
    ).filter(num_hilos__gt=0).order_by("-num_hilos", "name")[:5]


def hilos_populares():
    # Ejercicio 2: diez hilos con mayor puntuación (los votos ya existen).
    return hilos_visibles().order_by("-puntuacion", "-created_at")[:10]


def media_visitas_por_etiqueta():
    # Ejercicio 3: media por grupo, sin multiplicar filas por votos/respuestas.
    return Tag.objects.annotate(
        media_visitas=Avg("threads__views_count", filter=Q(
            threads__is_deleted=False, threads__merged_into__isnull=True
        )),
    ).values("name", "media_visitas").order_by("name")
