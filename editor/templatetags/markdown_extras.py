import markdown
import nh3
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


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

    return mark_safe(html_limpio)