import uuid

from django.core.files.storage import default_storage
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST
from PIL import Image

from .templatetags.markdown_extras import markdown_a_html

EXTENSIONES = {"jpeg": ".jpg", "png": ".png", "gif": ".gif", "webp": ".webp"}
MAX_BYTES = 5 * 1024 * 1024  # 5 MB


def probar_editor(request):
    return render(request, "editor/probar.html")


@require_POST
def vista_previa(request):
    texto = request.POST.get("texto", "")
    return JsonResponse({"html": str(markdown_a_html(texto))})


@require_POST
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