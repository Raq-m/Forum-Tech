import hashlib
import ipaddress
import socket
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

import requests
from django.core.cache import cache

MAX_BYTES = 512 * 1024   
MAX_REDIRECCIONES = 3
TIMEOUT = 5           


def _es_publica(host):
    """True solo si el servidor está en internet (no en una red interna)."""
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        return False
    for info in infos:
        ip = ipaddress.ip_address(info[4][0].split("%")[0])
        if not ip.is_global:
            return False
    return True


class _LectorMeta(HTMLParser):
    """Recoge las etiquetas <meta> y el <title> de una página."""

    def __init__(self):
        super().__init__()
        self.meta = {}
        self.titulo = ""
        self._en_title = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "meta":
            clave = (a.get("property") or a.get("name") or "").lower()
            if clave and a.get("content") and clave not in self.meta:
                self.meta[clave] = a["content"]
        elif tag == "title":
            self._en_title = True

    def handle_endtag(self, tag):
        if tag == "title":
            self._en_title = False

    def handle_data(self, data):
        if self._en_title:
            self.titulo += data


def _descargar(url):
    """Descarga la página comprobando CADA salto de redirección."""
    for _ in range(MAX_REDIRECCIONES + 1):
        p = urlparse(url)
        if p.scheme not in ("http", "https") or not p.hostname:
            return None
        try:
            if p.port not in (None, 80, 443):
                return None
        except ValueError:
            return None
        if not _es_publica(p.hostname):
            return None
        try:
            r = requests.get(
                url,
                headers={"User-Agent": "ForumTechBot/1.0"},
                timeout=TIMEOUT,
                stream=True,
                allow_redirects=False,
            )
        except requests.RequestException:
            return None
        if r.is_redirect:
            destino = r.headers.get("Location")
            r.close()
            if not destino:
                return None
            url = urljoin(url, destino)
            continue
        if "text/html" not in r.headers.get("Content-Type", ""):
            r.close()
            return None
        contenido = r.raw.read(MAX_BYTES, decode_content=True)
        r.close()
        return url, contenido.decode("utf-8", errors="replace")
    return None


def obtener_tarjeta(url):
    """Devuelve los datos de la tarjeta, o None si no se puede."""
    clave = "tarjeta:" + hashlib.sha256(url.encode()).hexdigest()
    guardado = cache.get(clave)
    if guardado is not None:
        return guardado or None

    resultado = None
    descarga = _descargar(url)
    if descarga:
        url_final, html = descarga
        lector = _LectorMeta()
        lector.feed(html)
        m = lector.meta
        titulo = m.get("og:title") or m.get("twitter:title") or lector.titulo.strip()
        descripcion = (
            m.get("og:description") or m.get("twitter:description")
            or m.get("description") or ""
        )
        imagen = m.get("og:image") or m.get("twitter:image") or ""
        if imagen:
            imagen = urljoin(url_final, imagen)
            if not imagen.startswith(("http://", "https://")):
                imagen = ""
        if titulo:
            resultado = {
                "url": url,
                "dominio": urlparse(url_final).hostname,
                "titulo": titulo[:150],
                "descripcion": descripcion[:250],
                "imagen": imagen,
            }

    cache.set(clave, resultado or {}, 3600)  
    return resultado