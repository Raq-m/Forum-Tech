from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import Notification, Reply, Thread


class ReplyNotificationTests(TestCase):
    def setUp(self):
        User = get_user_model()

        self.author = User.objects.create_user(
            username="thread_author",
            email="author@example.com",
            password="TestPassword123!",
        )
        self.other_user = User.objects.create_user(
            username="reply_author",
            email="reply@example.com",
            password="TestPassword123!",
        )
        self.thread = Thread.objects.create(
            author=self.author,
            title="Pregunta sobre Django",
            content="Contenido del hilo.",
        )

    def test_reply_notifies_thread_author(self):
        reply = Reply.objects.create(
            thread=self.thread,
            author=self.other_user,
            content="Una respuesta.",
        )

        self.assertEqual(Notification.objects.count(), 1)
        notification = Notification.objects.get()

        self.assertEqual(notification.recipient, self.author)
        self.assertEqual(notification.actor, self.other_user)
        self.assertEqual(notification.thread, self.thread)
        self.assertEqual(notification.reply, reply)
        self.assertEqual(notification.kind, Notification.Kind.REPLY)
        self.assertFalse(notification.is_read)

    def test_own_reply_does_not_create_notification(self):
        Reply.objects.create(
            thread=self.thread,
            author=self.author,
            content="Respondo a mi propio hilo.",
        )

        self.assertFalse(Notification.objects.exists())

    def test_editing_reply_does_not_duplicate_notification(self):
        reply = Reply.objects.create(
            thread=self.thread,
            author=self.other_user,
            content="Respuesta inicial.",
        )
        original_id = Notification.objects.get().pk

        reply.content = "Respuesta editada."
        reply.save()

        self.assertEqual(Notification.objects.count(), 1)
        self.assertEqual(Notification.objects.get().pk, original_id)


class NotificationViewTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.owner = User.objects.create_user(
            username="notice_owner",
            email="owner@example.com",
            password="TestPassword123!",
        )
        self.other = User.objects.create_user(
            username="notice_other",
            email="other@example.com",
            password="TestPassword123!",
        )
        self.thread = Thread.objects.create(
            author=self.owner,
            title="Hilo de prueba",
            content="Contenido.",
        )
        self.mine = Notification.objects.create(
            recipient=self.owner,
            actor=self.other,
            thread=self.thread,
            kind=Notification.Kind.MENTION,
        )
        self.foreign = Notification.objects.create(
            recipient=self.other,
            actor=self.owner,
            thread=self.thread,
            kind=Notification.Kind.MENTION,
        )

    def test_list_only_shows_own_notifications(self):
        from django.urls import reverse

        self.client.force_login(self.owner)
        response = self.client.get(reverse("forum:notifications"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            list(response.context["notifications"]),
            [self.mine],
        )

    def test_owner_can_mark_notification_read(self):
        from django.urls import reverse

        self.client.force_login(self.owner)
        response = self.client.post(
            reverse("forum:notification_mark_read", args=[self.mine.pk]),
        )

        self.assertRedirects(response, reverse("forum:notifications"))
        self.mine.refresh_from_db()
        self.assertTrue(self.mine.is_read)

    def test_cannot_mark_another_users_notification(self):
        from django.urls import reverse

        self.client.force_login(self.owner)
        response = self.client.post(
            reverse("forum:notification_mark_read", args=[self.foreign.pk]),
        )

        self.assertEqual(response.status_code, 404)
        self.foreign.refresh_from_db()
        self.assertFalse(self.foreign.is_read)

    def test_mark_read_rejects_get(self):
        from django.urls import reverse

        self.client.force_login(self.owner)
        response = self.client.get(
            reverse("forum:notification_mark_read", args=[self.mine.pk]),
        )

        self.assertEqual(response.status_code, 405)
        self.mine.refresh_from_db()
        self.assertFalse(self.mine.is_read)

    def test_notification_routes_require_login(self):
        from django.urls import reverse

        response = self.client.get(reverse("forum:notifications"))
        self.assertEqual(response.status_code, 302)

        response = self.client.post(
            reverse("forum:notification_mark_read", args=[self.mine.pk]),
        )
        self.assertEqual(response.status_code, 302)

        self.mine.refresh_from_db()
        self.assertFalse(self.mine.is_read)
