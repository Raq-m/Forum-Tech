from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Reply, Thread, UserFollow

User = get_user_model()


class SocialTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.ana = User.objects.create_user("ana", "ana@example.com", "clave-de-prueba-1")
        cls.luis = User.objects.create_user("luis", "luis@example.com", "clave-de-prueba-1")
        cls.hilo = Thread.objects.create(author=cls.ana, title="Duda", content="texto")
        cls.respuesta = Reply.objects.create(
            thread=cls.hilo, author=cls.luis, content="solución"
        )

    def test_el_autor_acepta_la_solucion(self):
        self.client.force_login(self.ana)
        url = reverse("forum:accept_solution", args=[self.respuesta.pk])
        respuesta = self.client.post(url)
        self.assertRedirects(
            respuesta, reverse("forum:thread_detail", args=[self.hilo.pk])
        )
        self.hilo.refresh_from_db()
        self.assertEqual(self.hilo.accepted_reply_id, self.respuesta.pk)

    def test_otro_usuario_no_puede_aceptar(self):
        self.client.force_login(self.luis)
        url = reverse("forum:accept_solution", args=[self.respuesta.pk])
        self.assertEqual(self.client.post(url).status_code, 403)
        self.hilo.refresh_from_db()
        self.assertIsNone(self.hilo.accepted_reply_id)

    def test_seguir_y_dejar_de_seguir(self):
        self.client.force_login(self.ana)
        url = reverse("forum:toggle_follow", args=["luis"])
        filtro = UserFollow.objects.filter(follower=self.ana, followed=self.luis)
        self.client.post(url)
        self.assertTrue(filtro.exists())
        self.client.post(url)
        self.assertFalse(filtro.exists())

    def test_no_puedes_seguirte_a_ti_mismo(self):
        self.client.force_login(self.ana)
        respuesta = self.client.post(reverse("forum:toggle_follow", args=["ana"]))
        self.assertEqual(respuesta.status_code, 400)
        self.assertFalse(UserFollow.objects.exists())

    def test_next_externo_se_ignora(self):
        self.client.force_login(self.ana)
        respuesta = self.client.post(
            reverse("forum:toggle_follow", args=["luis"]),
            {"next": "https://malo.example.com/"},
        )
        self.assertRedirects(
            respuesta, reverse("forum:thread_list"), fetch_redirect_response=False
        )

    def test_la_pagina_del_hilo_muestra_los_botones(self):
        self.client.force_login(self.ana)
        pagina = self.client.get(reverse("forum:thread_detail", args=[self.hilo.pk]))
        self.assertContains(pagina, "Aceptar como solución")
        self.assertContains(pagina, "Seguir")