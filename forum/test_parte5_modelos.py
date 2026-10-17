from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from .models import Reply, Tag, Thread, UserFollow
from .search import buscar_hilos, feed_siguiendo
from .solucion import aceptar_solucion

User = get_user_model()


class Parte5ModelosTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.ana = User.objects.create_user("ana", "ana@example.com", "clave-de-prueba-1")
        cls.luis = User.objects.create_user("luis", "luis@example.com", "clave-de-prueba-1")
        cls.hilo = Thread.objects.create(author=cls.ana, title="Duda con Django", content="vista")
        cls.otro = Thread.objects.create(author=cls.luis, title="Docker", content="contenedor")
        cls.respuesta = Reply.objects.create(thread=cls.hilo, author=cls.luis, content="Prueba así")

    def titulos(self, consulta):
        return [hilo.title for hilo in consulta]

    def test_etiquetas_desde_texto(self):
        etiquetas = Tag.desde_texto("#Python, django  python")
        self.assertEqual(sorted(t.name for t in etiquetas), ["django", "python"])

    def test_filtra_por_etiqueta(self):
        self.hilo.tags.set(Tag.desde_texto("django"))
        self.otro.tags.set(Tag.desde_texto("docker"))
        self.assertEqual(self.titulos(buscar_hilos(etiquetas=["#Django"])), ["Duda con Django"])

    def test_solucion_aceptada(self):
        aceptar_solucion(self.hilo, self.respuesta, self.ana)
        self.assertEqual(self.titulos(buscar_hilos(resuelto=True)), ["Duda con Django"])
        self.assertEqual(self.titulos(buscar_hilos(resuelto=False)), ["Docker"])

    def test_solo_el_autor_acepta_solucion(self):
        with self.assertRaises(PermissionDenied):
            aceptar_solucion(self.hilo, self.respuesta, self.luis)

    def test_respuesta_de_otro_hilo_no_vale(self):
        ajena = Reply.objects.create(thread=self.otro, author=self.ana, content="x")
        with self.assertRaises(ValidationError):
            aceptar_solucion(self.hilo, ajena, self.ana)

    def test_solucion_oculta_deja_de_contar_como_resuelto(self):
        aceptar_solucion(self.hilo, self.respuesta, self.ana)
        Reply.objects.filter(pk=self.respuesta.pk).update(is_deleted=True)
        self.assertEqual(self.titulos(buscar_hilos(resuelto=True)), [])

    def test_feed_siguiendo(self):
        UserFollow.objects.create(follower=self.ana, followed=self.luis)
        self.assertEqual(self.titulos(feed_siguiendo(self.ana)), ["Docker"])
        self.assertEqual(list(feed_siguiendo(self.luis)), [])

    def test_no_puedes_seguirte_a_ti_mismo(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            UserFollow.objects.create(follower=self.ana, followed=self.ana)