from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import Notification, Reply, ReplyVote, Thread


class VoteNotificationTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.author = User.objects.create_user(
            username="answer_author",
            email="answer@example.com",
        )
        self.voter = User.objects.create_user(
            username="answer_voter",
            email="voter@example.com",
        )
        self.thread = Thread.objects.create(
            author=self.author,
            title="Pregunta",
            content="Contenido.",
        )
        self.reply = Reply.objects.create(
            thread=self.thread,
            author=self.author,
            content="Respuesta.",
        )

    def create_vote(self, value, user=None):
        return ReplyVote.objects.create(
            reply=self.reply,
            user=user or self.voter,
            value=value,
        )

    def test_positive_vote_notifies_reply_author(self):
        self.create_vote(ReplyVote.Value.UP)

        notice = Notification.objects.get()
        self.assertEqual(notice.recipient, self.author)
        self.assertEqual(notice.actor, self.voter)
        self.assertEqual(notice.thread, self.thread)
        self.assertEqual(notice.reply, self.reply)
        self.assertEqual(notice.kind, Notification.Kind.VOTE)

    def test_repeated_positive_vote_does_not_duplicate_notice(self):
        vote = self.create_vote(ReplyVote.Value.UP)
        vote.save()

        self.assertEqual(Notification.objects.count(), 1)

    def test_negative_to_positive_creates_notice(self):
        vote = self.create_vote(ReplyVote.Value.DOWN)
        self.assertFalse(Notification.objects.exists())

        vote.value = ReplyVote.Value.UP
        vote.save()

        self.assertEqual(Notification.objects.count(), 1)

    def test_negative_vote_and_removal_do_not_create_notice(self):
        vote = self.create_vote(ReplyVote.Value.DOWN)
        vote.delete()

        self.assertFalse(Notification.objects.exists())

    def test_own_positive_vote_does_not_create_notice(self):
        self.create_vote(ReplyVote.Value.UP, user=self.author)

        self.assertFalse(Notification.objects.exists())

    def test_changing_to_negative_and_removing_adds_no_notice(self):
        vote = self.create_vote(ReplyVote.Value.UP)
        notice_id = Notification.objects.get().pk

        vote.value = ReplyVote.Value.DOWN
        vote.save()
        vote.delete()

        self.assertEqual(Notification.objects.count(), 1)
        self.assertEqual(Notification.objects.get().pk, notice_id)