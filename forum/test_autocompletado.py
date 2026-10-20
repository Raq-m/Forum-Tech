from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Thread

User = get_user_model()


class AutocompletadoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.ana = User.objects.create_user("ana", "ana@example.com", "clave-de-prueba-1")
        cls.hilo_django = Thread.objects.create(
            author=cls.ana, title="Duda con Django", content="x"
        )
        Thread.objects.create(author=cls.ana, title="Docker no arranca", content="x")
        Thread.objects.create(
            author=cls.ana, title="Django oculto", content="x", is_deleted=True
        )

    def sugerencias(self, texto):
        respuesta = self.client.get(reverse("forum:thread_suggest"), {"q": texto})
        self.assertEqual(respuesta.status_code, 200)
        return respuesta.json()["resultados"]

    def test_sugiere_por_titulo_con_su_enlace(self):
        resultados = self.sugerencias("djan")
        self.assertEqual([r["titulo"] for r in resultados], ["Duda con Django"])
        self.assertEqual(
            resultados[0]["url"],
            reverse("forum:thread_detail", args=[self.hilo_django.pk]),
        )

    def test_no_sugiere_hilos_ocultos(self):
        self.assertEqual(self.sugerencias("oculto"), [])

    def test_con_menos_de_dos_letras_no_devuelve_nada(self):
        self.assertEqual(self.sugerencias("d"), [])

    def test_varias_palabras_deben_estar_todas(self):
        self.assertEqual(len(self.sugerencias("duda django")), 1)
        self.assertEqual(self.sugerencias("duda docker"), [])

    def test_la_pagina_de_hilos_incluye_el_buscador_con_sugerencias(self):
        pagina = self.client.get(reverse("forum:thread_list"))
        self.assertContains(pagina, 'id="sugerencias"')