from datetime import date

from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse

from .models import Thread
from .search import buscar_hilos, hilos_visibles

FEEDS = [
    ("nuevos", "Nuevos"),
    ("populares", "Populares"),
    ("sin-respuesta", "Sin respuesta"),
    ("siguiendo", "Siguiendo"),
]
POR_PAGINA = 10
MAX_SUGERENCIAS = 8


def _fecha(texto):
    try:
        return date.fromisoformat(texto) if texto else None
    except ValueError:
        return None


def _entero(texto):
    try:
        return int(texto) if texto else None
    except ValueError:
        return None


def thread_list(request):
    datos = request.GET
    feed = datos.get("feed", "nuevos")
    if feed not in dict(FEEDS):
        feed = "nuevos"

    q = datos.get("q", "").strip()
    autor = datos.get("autor", "").strip()
    etiquetas = datos.get("etiquetas", "").strip()
    desde = datos.get("desde", "")
    hasta = datos.get("hasta", "")
    min_votos = datos.get("min_votos", "")
    estado = datos.get("estado", "")

    aviso = ""
    if feed == "siguiendo" and not request.user.is_authenticated:
        hilos = Thread.objects.none()
        aviso = "Inicia sesión para ver los hilos de las personas que sigues."
    else:
        hilos = buscar_hilos(
            texto=q,
            autor=autor,
            desde=_fecha(desde),
            hasta=_fecha(hasta),
            min_votos=_entero(min_votos),
            etiquetas=etiquetas.replace(",", " ").split(),
            resuelto={"resuelto": True, "sin-resolver": False}.get(estado),
        )

        if feed == "populares":
            hilos = hilos.order_by("-puntuacion", "-num_respuestas", "-created_at")
        elif feed == "sin-respuesta":
            hilos = hilos.filter(num_respuestas=0)
        elif feed == "siguiendo":
            hilos = hilos.filter(author__follows_received__follower=request.user)
        hilos = hilos.prefetch_related("tags")

    pagina = Paginator(hilos, POR_PAGINA).get_page(datos.get("page"))
    parametros = datos.copy()
    parametros.pop("page", None)

    return render(request, "forum/thread_list.html", {
        "feeds": FEEDS,
        "feed": feed,
        "pagina": pagina,
        "q": q,
        "autor": autor,
        "etiquetas": etiquetas,
        "desde": desde,
        "hasta": hasta,
        "min_votos": min_votos,
        "estado": estado,
        "aviso": aviso,
        "querystring": parametros.urlencode(),
    })


def thread_suggest(request):
    """Sugerencias de títulos mientras se escribe en el buscador."""
    q = request.GET.get("q", "").strip()
    if len(q) < 2:
        return JsonResponse({"resultados": []})

    hilos = hilos_visibles()
    for palabra in q.split():
        hilos = hilos.filter(title__icontains=palabra)
    hilos = hilos.order_by("-puntuacion", "-created_at")[:MAX_SUGERENCIAS]

    return JsonResponse({
        "resultados": [
            {
                "titulo": hilo.title,
                "url": reverse("forum:thread_detail", args=[hilo.pk]),
            }
            for hilo in hilos
        ]
    })