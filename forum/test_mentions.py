from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import Notification, Reply, Thread


class MentionNotificationTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.author = User.objects.create_user(
            username="author",
            email="author@example.com",
        )
        self.writer = User.objects.create_user(
            username="writer",
            email="writer@example.com",
        )
        self.reader = User.objects.create_user(
            username="reader",
            email="reader@example.com",
        )

    def test_thread_mentions_ignore_case_and_repetitions(self):
        thread = Thread.objects.create(
            author=self.author,
            title="Menciones",
            content="@reader @READER @author @unknown",
        )

        self.assertEqual(Notification.objects.count(), 1)
        notice = Notification.objects.get()
        self.assertEqual(notice.recipient, self.reader)
        self.assertEqual(notice.actor, self.author)
        self.assertEqual(notice.thread, thread)
        self.assertIsNone(notice.reply)
        self.assertEqual(notice.kind, Notification.Kind.MENTION)

    def test_reply_mentions_do_not_duplicate_author_notice(self):
        thread = Thread.objects.create(
            author=self.author,
            title="Pregunta",
            content="Contenido.",
        )
        reply = Reply.objects.create(
            thread=thread,
            author=self.writer,
            content="@author @reader @READER @writer",
        )

        self.assertEqual(Notification.objects.count(), 2)

        author_notice = Notification.objects.get(recipient=self.author)
        self.assertEqual(author_notice.kind, Notification.Kind.REPLY)

        reader_notice = Notification.objects.get(recipient=self.reader)
        self.assertEqual(reader_notice.kind, Notification.Kind.MENTION)
        self.assertEqual(reader_notice.reply, reply)

    def test_edit_does_not_generate_new_mentions(self):
        thread = Thread.objects.create(
            author=self.author,
            title="Pregunta",
            content="Sin menciones.",
        )
        thread.content = "@reader"
        thread.save()

        self.assertFalse(Notification.objects.exists())

    def test_inactive_user_is_not_notified(self):
        self.reader.is_active = False
        self.reader.save(update_fields=["is_active"])

        Thread.objects.create(
            author=self.author,
            title="Pregunta",
            content="@reader",
        )

        self.assertFalse(Notification.objects.exists())