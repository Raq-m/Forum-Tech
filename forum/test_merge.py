from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from .models import Notification, Reply, ReplyVote, Thread
from .services import merge_threads


class ThreadMergeTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.author = User.objects.create_user(
            username="merge_author",
            email="merge-author@example.com",
        )
        self.moderator = User.objects.create_user(
            username="merge_moderator",
            email="merge-moderator@example.com",
        )
        self.moderator.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="forum",
                content_type__model="thread",
                codename="change_thread",
            )
        )

        self.source = Thread.objects.create(
            author=self.author,
            title="Origen",
            content="Texto original.",
        )
        self.target = Thread.objects.create(
            author=self.author,
            title="Destino",
            content="Texto de destino.",
        )
        self.reply = Reply.objects.create(
            thread=self.source,
            author=self.author,
            content="Respuesta que se mueve.",
        )
        self.url = reverse(
            "forum:thread_merge",
            args=[self.source.pk],
        )

    def test_merge_preserves_reply_votes_and_updates_notifications(self):
        vote = ReplyVote.objects.create(
            reply=self.reply,
            user=self.moderator,
            value=ReplyVote.Value.UP,
        )
        notice = Notification.objects.get(
            reply=self.reply,
            kind=Notification.Kind.VOTE,
        )

        moved = merge_threads(self.source.pk, self.target.pk)

        self.assertEqual(moved, 1)
        self.reply.refresh_from_db()
        self.source.refresh_from_db()
        notice.refresh_from_db()

        self.assertEqual(self.reply.thread_id, self.target.pk)
        self.assertTrue(ReplyVote.objects.filter(pk=vote.pk).exists())
        self.assertEqual(notice.thread_id, self.target.pk)
        self.assertEqual(self.source.merged_into_id, self.target.pk)
        self.assertTrue(self.source.is_locked)
        self.assertEqual(self.source.content, "Texto original.")

    def test_old_thread_url_redirects_to_target(self):
        merge_threads(self.source.pk, self.target.pk)

        response = self.client.get(
            reverse("forum:thread_detail", args=[self.source.pk]),
        )

        self.assertRedirects(
            response,
            reverse("forum:thread_detail", args=[self.target.pk]),
        )

    def test_regular_user_cannot_merge(self):
        self.client.force_login(self.author)

        response = self.client.post(
            self.url,
            {"target": self.target.pk, "confirm": "on"},
        )

        self.assertEqual(response.status_code, 403)
        self.reply.refresh_from_db()
        self.assertEqual(self.reply.thread_id, self.source.pk)

    def test_moderator_can_merge_after_confirmation(self):
        self.client.force_login(self.moderator)

        response = self.client.post(
            self.url,
            {"target": self.target.pk, "confirm": "on"},
        )

        self.assertRedirects(
            response,
            reverse("forum:thread_detail", args=[self.target.pk]),
        )

    def test_confirmation_is_required(self):
        self.client.force_login(self.moderator)

        response = self.client.post(
            self.url,
            {"target": self.target.pk},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("confirm", response.context["form"].errors)
        self.source.refresh_from_db()
        self.assertIsNone(self.source.merged_into_id)

    def test_invalid_destinations_are_rejected(self):
        with self.assertRaises(ValidationError):
            merge_threads(self.source.pk, self.source.pk)

        self.target.is_locked = True
        self.target.save(update_fields=["is_locked"])

        with self.assertRaises(ValidationError):
            merge_threads(self.source.pk, self.target.pk)

        self.target.is_locked = False
        self.target.is_deleted = True
        self.target.save(update_fields=["is_locked", "is_deleted"])

        with self.assertRaises(ValidationError):
            merge_threads(self.source.pk, self.target.pk)

        self.reply.refresh_from_db()
        self.assertEqual(self.reply.thread_id, self.source.pk)

    def test_reverse_merge_is_rejected(self):
        merge_threads(self.source.pk, self.target.pk)

        with self.assertRaises(ValidationError):
            merge_threads(self.target.pk, self.source.pk)
            