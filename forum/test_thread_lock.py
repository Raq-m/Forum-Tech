from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Reply, Thread


class ThreadLockTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.author = User.objects.create_user(
            username="lock_author",
            email="lock-author@example.com",
        )
        self.writer = User.objects.create_user(
            username="lock_writer",
            email="lock-writer@example.com",
        )
        self.thread = Thread.objects.create(
            author=self.author,
            title="Prueba de bloqueo",
            content="Contenido.",
        )
        self.url = reverse(
            "forum:reply_create",
            args=[self.thread.pk],
        )

    def test_open_thread_accepts_reply_with_server_assigned_author(self):
        self.client.force_login(self.writer)

        response = self.client.post(
            self.url,
            {
                "content": "Nueva respuesta.",
                "author": self.author.pk,
            },
        )

        self.assertRedirects(
            response,
            reverse("forum:thread_detail", args=[self.thread.pk]),
        )
        reply = Reply.objects.get()
        self.assertEqual(reply.author, self.writer)
        self.assertEqual(reply.thread, self.thread)

    def test_locked_thread_rejects_reply(self):
        self.thread.is_locked = True
        self.thread.save(update_fields=["is_locked"])
        self.client.force_login(self.writer)

        response = self.client.post(
            self.url,
            {"content": "Intento responder."},
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(Reply.objects.exists())

    def test_unlocking_allows_reply_again(self):
        self.thread.is_locked = True
        self.thread.save(update_fields=["is_locked"])
        self.client.force_login(self.writer)

        self.assertEqual(
            self.client.post(
                self.url,
                {"content": "Intento bloqueado."},
            ).status_code,
            403,
        )

        self.thread.is_locked = False
        self.thread.save(update_fields=["is_locked"])

        response = self.client.post(
            self.url,
            {"content": "Ahora puedo responder."},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Reply.objects.count(), 1)

    def test_login_is_required(self):
        response = self.client.post(
            self.url,
            {"content": "Sin iniciar sesion."},
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(Reply.objects.exists())

    def test_get_does_not_create_reply(self):
        self.client.force_login(self.writer)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 405)
        self.assertFalse(Reply.objects.exists())

    def test_empty_reply_is_rejected(self):
        self.client.force_login(self.writer)

        response = self.client.post(
            self.url,
            {"content": "   "},
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("content", response.context["form"].errors)
        self.assertFalse(Reply.objects.exists())