import uuid
from functools import wraps

from .enlaces import obtener_tarjeta

from django.core.files.storage import default_storage
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST
from PIL import Image

from .templatetags.markdown_extras import markdown_a_html

def login_json(vista):
    """Si no has iniciado sesión, responde 401 en vez de ejecutar la vista."""
    @wraps(vista)
    def envoltura(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Debes iniciar sesión."}, status=401)
        return vista(request, *args, **kwargs)
    return envoltura

EXTENSIONES = {"jpeg": ".jpg", "png": ".png", "gif": ".gif", "webp": ".webp"}
MAX_BYTES = 5 * 1024 * 1024  # 5 MB


def probar_editor(request):
    return render(request, "editor/probar.html")


@require_POST
def vista_previa(request):
    texto = request.POST.get("texto", "")
    return JsonResponse({"html": str(markdown_a_html(texto))})


@require_POST
@login_json
def subir_imagen(request):
    archivo = request.FILES.get("imagen")
    if archivo is None:
        return JsonResponse({"error": "No se envió ninguna imagen."}, status=400)
    if archivo.size > MAX_BYTES:
        return JsonResponse({"error": "La imagen pesa más de 5 MB."}, status=400)

    try:
        imagen = Image.open(archivo)
        formato = (imagen.format or "").lower()
        imagen.verify()
    except Exception:
        return JsonResponse({"error": "El archivo no es una imagen válida."}, status=400)

    if formato not in EXTENSIONES:
        return JsonResponse({"error": "Formato no permitido."}, status=400)


    archivo.seek(0)
    nombre = f"editor/{uuid.uuid4().hex}{EXTENSIONES[formato]}"
    ruta = default_storage.save(nombre, archivo)
    return JsonResponse({"url": default_storage.url(ruta)})

@require_POST
@login_json
def previsualizar_enlace(request):
    tarjeta = obtener_tarjeta(request.POST.get("url", ""))
    if tarjeta is None:
        return JsonResponse({"error": "Sin previsualización."}, status=400)
    return JsonResponse(tarjeta)