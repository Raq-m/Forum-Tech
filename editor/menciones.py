import re
from django.db.models import Q

from django.contrib.auth import get_user_model


MENCION_RE = re.compile(r"(?<![\w@/.-])@(\w+(?:[.-]\w+)*)")


PROTEGIDO_RE = re.compile(
    r"(<pre.*?</pre>|<code.*?</code>|<a\s.*?</a>|<[^>]+>)", re.DOTALL
)


def extraer_menciones(texto):
    """Devuelve {nombre_en_minúsculas: nombre_real} de los usuarios que existen."""
    candidatos = set(MENCION_RE.findall(texto or ""))
    if not candidatos:
        return {}
    filtro = Q()
    for nombre in candidatos:
        filtro |= Q(username__iexact=nombre)  # iexact = ignora mayúsculas
    User = get_user_model()
    reales = User.objects.filter(filtro).values_list("username", flat=True)
    return {nombre.lower(): nombre for nombre in reales}


def resaltar_menciones(html, usuarios):
    """Envuelve cada @usuario existente en un <span class="mencion">."""
    if not usuarios:
        return html

    def cambiar(coincidencia):
        real = usuarios.get(coincidencia.group(1).lower())
        if real:
            return f'<span class="mencion">@{real}</span>'
        return coincidencia.group(0)

    partes = PROTEGIDO_RE.split(html)
    for i, parte in enumerate(partes):
        if not parte.startswith("<"):
            partes[i] = MENCION_RE.sub(cambiar, parte)
    return "".join(partes)