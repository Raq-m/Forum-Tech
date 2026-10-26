from django_filters import rest_framework as filters

from forum.models import Thread


class ThreadFilter(filters.FilterSet):
    author = filters.CharFilter(field_name="author__username", lookup_expr="iexact")
    tag = filters.CharFilter(field_name="tags__name", lookup_expr="iexact")
    min_votes = filters.NumberFilter(field_name="puntuacion", lookup_expr="gte")
    max_votes = filters.NumberFilter(field_name="puntuacion", lookup_expr="lte")
    min_views = filters.NumberFilter(field_name="views_count", lookup_expr="gte")
    max_views = filters.NumberFilter(field_name="views_count", lookup_expr="lte")
    resolved = filters.BooleanFilter(field_name="esta_resuelto")

    class Meta:
        model = Thread
        fields = ["is_locked"]
