from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Reply, ReplyVote, Report, Thread, ThreadVote


class SoftDeleteTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="soft_delete_user",
            email="soft-delete@example.com",
        )
        self.thread = Thread.objects.create(
            author=self.user,
            title="Hilo de prueba",
            content="Contenido.",
        )
        self.reply = Reply.objects.create(
            thread=self.thread,
            author=self.user,
            content="Respuesta que se puede ocultar.",
        )
        self.client.force_login(self.user)

    def test_deleted_thread_rejects_public_access_and_actions(self):
        self.thread.is_deleted = True
        self.thread.save(update_fields=["is_deleted"])

        response = self.client.get(
            reverse("forum:thread_detail", args=[self.thread.pk]),
        )
        self.assertEqual(response.status_code, 404)

        cases = [
            ("forum:vote_thread", self.thread.pk, {"value": "1"}),
            ("forum:report_thread", self.thread.pk, {"reason": "spam"}),
            ("forum:reply_create", self.thread.pk, {"content": "Nueva"}),
            ("forum:vote_reply", self.reply.pk, {"value": "1"}),
            ("forum:report_reply", self.reply.pk, {"reason": "spam"}),
        ]

        for route, pk, data in cases:
            with self.subTest(route=route):
                response = self.client.post(
                    reverse(route, args=[pk]),
                    data,
                )
                self.assertEqual(response.status_code, 404)

        self.assertEqual(Reply.objects.count(), 1)
        self.assertFalse(ThreadVote.objects.exists())
        self.assertFalse(ReplyVote.objects.exists())
        self.assertFalse(Report.objects.exists())

    def test_deleted_reply_is_hidden_and_rejects_actions(self):
        self.reply.is_deleted = True
        self.reply.save(update_fields=["is_deleted"])

        response = self.client.get(
            reverse("forum:thread_detail", args=[self.thread.pk]),
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, self.reply.content)

        for route, data in [
            ("forum:vote_reply", {"value": "1"}),
            ("forum:report_reply", {"reason": "spam"}),
        ]:
            with self.subTest(route=route):
                response = self.client.post(
                    reverse(route, args=[self.reply.pk]),
                    data,
                )
                self.assertEqual(response.status_code, 404)

        self.assertFalse(ReplyVote.objects.exists())
        self.assertFalse(Report.objects.exists())
        self.assertTrue(Reply.objects.filter(pk=self.reply.pk).exists())

    def test_restoring_reply_makes_it_visible_again(self):
        self.reply.is_deleted = True
        self.reply.save(update_fields=["is_deleted"])

        self.reply.is_deleted = False
        self.reply.save(update_fields=["is_deleted"])

        response = self.client.get(
            reverse("forum:thread_detail", args=[self.thread.pk]),
        )

        self.assertContains(response, self.reply.content)
        