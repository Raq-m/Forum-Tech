from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from forum.models import Reply, Tag, Thread, ThreadVote, UserFollow
from forum.solucion import aceptar_solucion

User = get_user_model()


def crear_hilo(autor, titulo, contenido, etiquetas, dias):
    hilo = Thread.objects.create(author=autor, title=titulo, content=contenido)
    hilo.tags.set(Tag.desde_texto(etiquetas))
    # created_at se rellena solo; lo retrasamos para tener fechas distintas
    Thread.objects.filter(pk=hilo.pk).update(
        created_at=timezone.now() - timedelta(days=dias)
    )
    return hilo


class Command(BaseCommand):
    help = "Crea datos de prueba para ver el foro."

    def add_arguments(self, parser):
        parser.add_argument(
            "--usuario",
            help="Usuario que seguirá a demo_luis (para probar la pestaña Siguiendo).",
        )

    @transaction.atomic
    def handle(self, *args, **opciones):
        if User.objects.filter(username="demo_ana").exists():
            self.stdout.write("Los datos de prueba ya existían; no se crea nada nuevo.")
        else:
            self.crear_datos()
            self.stdout.write(self.style.SUCCESS("Datos de prueba creados."))

        nombre = opciones.get("usuario")
        if nombre:
            usuario = User.objects.filter(username=nombre).first()
            luis = User.objects.get(username="demo_luis")
            if usuario is None:
                self.stdout.write(self.style.ERROR(f"No existe el usuario {nombre}."))
            else:
                UserFollow.objects.get_or_create(follower=usuario, followed=luis)
                self.stdout.write(f"{nombre} ahora sigue a demo_luis.")

    def crear_datos(self):
        ana, luis, marta = (
            User.objects.create_user(n, f"{n}@example.com", "demo-1234")
            for n in ("demo_ana", "demo_luis", "demo_marta")
        )

        h1 = crear_hilo(
            ana, "Duda con Django y las vistas",
            "¿Cómo paso datos de una vista a la plantilla?",
            "django python", 5,
        )
        h2 = crear_hilo(
            luis, "Docker no arranca el contenedor",
            "Me sale un error al hacer docker compose up.",
            "docker", 4,
        )
        crear_hilo(
            marta, "Cómo uso Git para fusionar ramas",
            "Me cuesta entender la diferencia entre merge y rebase.",
            "git", 3,
        )
        crear_hilo(
            ana, "Mejor editor para empezar con Python",
            "¿VSCode o PyCharm? Soy principiante.",
            "python herramientas", 2,
        )
        h5 = crear_hilo(
            luis, "Consultas con el ORM de Django",
            "¿Cómo filtro por un campo de otra tabla?",
            "django bases-de-datos", 1,
        )

        r1 = Reply.objects.create(
            thread=h1, author=luis,
            content="Pásalas en el diccionario de contexto de render.",
        )
        Reply.objects.create(
            thread=h1, author=marta,
            content="Mira la documentación de render y de las plantillas.",
        )
        Reply.objects.create(
            thread=h2, author=ana,
            content="Comprueba que el puerto no esté ocupado.",
        )
        Reply.objects.create(
            thread=h5, author=marta,
            content="Usa la doble barra baja entre los nombres de los campos.",
        )

        ThreadVote.objects.create(thread=h1, user=luis, value=1)
        ThreadVote.objects.create(thread=h1, user=marta, value=1)
        ThreadVote.objects.create(thread=h2, user=ana, value=1)
        ThreadVote.objects.create(thread=h5, user=ana, value=-1)

        aceptar_solucion(h1, r1, ana)
        UserFollow.objects.create(follower=ana, followed=luis)