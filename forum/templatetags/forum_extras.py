from django import template

from forum.models import UserFollow

register = template.Library()


@register.simple_tag
def sigue_a(usuario, autor):
    """True si `usuario` sigue a `autor`."""
    if not usuario.is_authenticated or usuario.pk == autor.pk:
        return False
    return UserFollow.objects.filter(follower=usuario, followed=autor).exists()