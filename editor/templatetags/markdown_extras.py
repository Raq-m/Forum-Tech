import re

import markdown
import nh3
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

# Busca un párrafo que sea SOLO un enlace de YouTube
YOUTUBE_RE = re.compile(
    r"<p>\s*https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)"
    r"([\w-]{11})[^<\s]*\s*</p>"
)


def _incrustar_youtube(coincidencia):
    id_video = coincidencia.group(1)
    return (
        '<div class="video"><iframe '
        f'src="https://www.youtube-nocookie.com/embed/{id_video}" '
        'title="Vídeo de YouTube" loading="lazy" '
        'referrerpolicy="strict-origin-when-cross-origin" '
        'allow="accelerometer; autoplay; clipboard-write; encrypted-media; '
        'gyroscope; picture-in-picture; web-share" '
        "allowfullscreen></iframe></div>"
    )


@register.filter(name="markdown")
def markdown_a_html(texto):
  
    html = markdown.markdown(
        texto or "",
        extensions=["fenced_code", "codehilite", "tables", "nl2br"],
        extension_configs={
            "codehilite": {"css_class": "codehilite", "guess_lang": False}
        },
    )
    html_limpio = nh3.clean(
        html,
        attributes={
            "*": {"class"},
            "a": {"href", "title"},
            "img": {"src", "alt", "title"},
        },
    )

    html_limpio = YOUTUBE_RE.sub(_incrustar_youtube, html_limpio)
 
    return mark_safe(html_limpio)