from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import Reply, Thread, ThreadVote
from .search import buscar_hilos, feed_populares, feed_sin_respuesta

User = get_user_model()


class BusquedaTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.ana = User.objects.create_user("ana", "ana@example.com", "clave-de-prueba-1")
        cls.luis = User.objects.create_user("luis", "luis@example.com", "clave-de-prueba-1")
        cls.hilo_django = Thread.objects.create(
            author=cls.ana, title="Duda con Django", content="¿Cómo hago una vista?"
        )
        cls.hilo_docker = Thread.objects.create(
            author=cls.luis, title="Docker", content="Error al arrancar el contenedor"
        )

    def titulos(self, consulta):
        return [hilo.title for hilo in consulta]

    def test_busca_en_titulo_y_contenido(self):
        self.assertEqual(self.titulos(buscar_hilos("django")), ["Duda con Django"])
        self.assertEqual(self.titulos(buscar_hilos("contenedor")), ["Docker"])

    def test_excluye_ocultos_y_fusionados(self):
        Thread.objects.create(author=self.ana, title="Django oculto", content="x", is_deleted=True)
        Thread.objects.create(
            author=self.ana, title="Django fusionado", content="x", merged_into=self.hilo_django
        )
        self.assertEqual(self.titulos(buscar_hilos("django")), ["Duda con Django"])

    def test_busca_en_respuestas_visibles(self):
        Reply.objects.create(thread=self.hilo_docker, author=self.ana, content="Prueba con kubernetes")
        Reply.objects.create(thread=self.hilo_django, author=self.ana, content="Usa postgres", is_deleted=True)
        self.assertEqual(self.titulos(buscar_hilos("kubernetes")), ["Docker"])
        self.assertEqual(self.titulos(buscar_hilos("postgres")), [])

    def test_filtra_por_autor(self):
        self.assertEqual(self.titulos(buscar_hilos(autor="LUIS")), ["Docker"])

    def test_populares_y_sin_respuesta_no_multiplican_filas(self):
        for _ in range(2):
            Reply.objects.create(thread=self.hilo_docker, author=self.ana, content="respuesta")
        ThreadVote.objects.create(thread=self.hilo_docker, user=self.ana, value=1)
        ThreadVote.objects.create(thread=self.hilo_docker, user=self.luis, value=1)

        populares = list(feed_populares())
        self.assertEqual(populares[0].title, "Docker")
        self.assertEqual(populares[0].puntuacion, 2)
        self.assertEqual(populares[0].num_respuestas, 2)
        self.assertEqual(self.titulos(feed_sin_respuesta()), ["Duda con Django"])