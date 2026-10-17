from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Reply, ReplyVote, Report, Thread, ThreadVote


class SuspensionTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.author = User.objects.create_user(
            username="suspension_author",
            email="suspension-author@example.com",
        )
        self.user = User.objects.create_user(
            username="suspension_user",
            email="suspension-user@example.com",
        )
        self.thread = Thread.objects.create(
            author=self.author,
            title="Prueba de suspension",
            content="Contenido.",
        )
        self.reply = Reply.objects.create(
            thread=self.thread,
            author=self.author,
            content="Respuesta.",
        )
        self.client.force_login(self.user)

    def suspend(self, until):
        get_user_model().objects.filter(pk=self.user.pk).update(
            suspended_until=until,
        )

    def test_existing_session_cannot_perform_forum_actions(self):
        self.suspend(timezone.now() + timedelta(days=1))

        cases = [
            ("forum:vote_thread", self.thread.pk, {"value": "1"}),
            ("forum:vote_reply", self.reply.pk, {"value": "1"}),
            ("forum:reply_create", self.thread.pk, {"content": "Nueva"}),
            ("forum:report_thread", self.thread.pk, {"reason": "spam"}),
            ("forum:report_reply", self.reply.pk, {"reason": "spam"}),
        ]

        for route, pk, data in cases:
            with self.subTest(route=route):
                response = self.client.post(
                    reverse(route, args=[pk]),
                    data,
                )
                self.assertEqual(response.status_code, 403)

        self.assertEqual(Reply.objects.count(), 1)
        self.assertFalse(ThreadVote.objects.exists())
        self.assertFalse(ReplyVote.objects.exists())
        self.assertFalse(Report.objects.exists())

    def test_suspended_user_can_read_and_view_notifications(self):
        self.suspend(timezone.now() + timedelta(days=1))

        for url in [
            reverse("forum:thread_detail", args=[self.thread.pk]),
            reverse("forum:notifications"),
        ]:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_expired_suspension_allows_reply(self):
        self.suspend(timezone.now() - timedelta(seconds=1))

        response = self.client.post(
            reverse("forum:reply_create", args=[self.thread.pk]),
            {"content": "La suspension ha terminado."},
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            Reply.objects.filter(
                author=self.user,
                content="La suspension ha terminado.",
            ).exists()
        )

    def test_suspension_property(self):
        self.user.suspended_until = None
        self.assertFalse(self.user.is_suspended)

        self.user.suspended_until = timezone.now() + timedelta(days=1)
        self.assertTrue(self.user.is_suspended)

        self.user.suspended_until = timezone.now() - timedelta(seconds=1)
        self.assertFalse(self.user.is_suspended)
        