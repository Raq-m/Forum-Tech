# Editor de contenido (módulo 3 - Raquel)

App Django `editor`. Convierte el texto Markdown que escriben los usuarios en HTML seguro, con código coloreado, imágenes, vídeos, menciones y tarjetas de enlaces.

## Cómo usarlo en una plantilla

```
{% load markdown_extras %}
{{ hilo.contenido|markdown }}
```

`hilo.contenido` es un ejemplo: se pone el campo donde se guarde el texto.

Para escribir, `editor/templates/editor/probar.html` es la página de prueba y sirve de modelo (caja de texto, vista previa, botones, subida de imágenes y tarjetas). Su JavaScript está dentro de la propia página: para reutilizarlo en el foro habrá que moverlo a un archivo estático.

## Qué incluye

- Markdown con vista previa en vivo, botones y atajos (Ctrl+B, Ctrl+I, Ctrl+K)
- Bloques de código con colores (`editor/static/editor/codehilite.css`)
- Imágenes y GIFs por arrastrar y soltar (se guardan en `media/editor/`)
- Vídeos de YouTube (enlace solo en una línea)
- Tarjetas de previsualización de enlaces (OpenGraph)
- Menciones `@usuario` (solo si el usuario existe; no distingue mayúsculas)

## Archivos principales

- `templatetags/markdown_extras.py`: el filtro `|markdown`
- `menciones.py`: detecta y resalta menciones (`extraer_menciones`, `resaltar_menciones`) - probado con nuestros superusuarios
- `enlaces.py`: lee título, descripción e imagen de una web (bloquea direcciones internas)
- `views.py` y `urls.py`: vista previa, subida de imágenes y tarjetas

## Requisitos

- Librerías en `requirements.txt` (Markdown, Pygments, nh3, Pillow, requests)
- `python manage.py migrate` (las menciones consultan la tabla de usuarios)
- `MEDIA_URL` y `MEDIA_ROOT` en `config/settings/base.py`

## Seguridad

- El HTML se limpia con `nh3`; los vídeos y tarjetas se añaden después, solo con datos validados.
- Subir imágenes y pedir tarjetas exigen sesión iniciada (si no, responden 401).

## Pendiente

| Qué falta | Módulo |
|---|---|
| Menciones `#id_hilo` | Módulo 2: Estructura de Contenidos y Navegación (necesita los hilos) |
| Usar el editor al crear hilos y respuestas | Módulo 2 |
| Notificar al usuario mencionado | Módulo 4: Interacción, Moderación y Comunidad (usar `extraer_menciones`) |
| Que `@usuario` enlace a su perfil | Módulo 1: Usuarios y Perfiles (necesita páginas de perfil) |
| Redirigir al login en vez de responder 401 | Módulo 1 (necesita las páginas de login) |