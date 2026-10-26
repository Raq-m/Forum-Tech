from django.core.management.base import BaseCommand

from forum.search import hilos_visibles
from forum.statistics import (
    etiquetas_populares, hilos_populares, media_visitas_por_etiqueta, resumen_foro,
)


class Command(BaseCommand):
    help = "Estadísticas, SQL y EXPLAIN de solo lectura para la sesión 7."

    def handle(self, *args, **options):
        self.stdout.write(str(resumen_foro()))
        self.stdout.write(str(list(etiquetas_populares().values("name", "num_hilos"))))
        self.stdout.write(str(list(hilos_populares().values("title", "puntuacion"))))
        self.stdout.write(str(list(media_visitas_por_etiqueta())))
        consulta = hilos_visibles().order_by("-created_at")
        self.stdout.write(str(consulta.query))
        self.stdout.write(consulta.explain())
