from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase

from .models import Reply, ReplyVote, Thread, ThreadVote
class VoteModelTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.author = User.objects.create_user(
            username="author_test",
            email="author@example.com",
            password="TestPassword123!",
        )
        self.voter = User.objects.create_user(
            username="voter_test",
            email="voter@example.com",
            password="TestPassword123!",
        )
        self.thread = Thread.objects.create(
            author=self.author,
            title="Pregunta sobre Django",
            content="¿Cómo funcionan las migraciones?",
        )
        self.reply = Reply.objects.create(
            thread=self.thread,
            author=self.author,
            content="Las migraciones actualizan la estructura de la BD.",
        )

    def test_thread_vote_can_be_created(self):
        vote = ThreadVote.objects.create(
            thread=self.thread,
            user=self.voter,
            value=ThreadVote.Value.UP,
        )
        vote.refresh_from_db()
        self.assertEqual(vote.value, 1)
        self.assertEqual(self.thread.votes.count(), 1)

    def test_reply_vote_can_be_created(self):
        vote = ReplyVote.objects.create(
            reply=self.reply,
            user=self.voter,
            value=ReplyVote.Value.DOWN,
        )
        vote.refresh_from_db()
        self.assertEqual(vote.value, -1)
        self.assertEqual(self.reply.votes.count(), 1)

    def test_duplicate_thread_vote_is_rejected(self):
        ThreadVote.objects.create(
            thread=self.thread,
            user=self.voter,
            value=ThreadVote.Value.UP,
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                ThreadVote.objects.create(
                    thread=self.thread,
                    user=self.voter,
                    value=ThreadVote.Value.DOWN,
                )

    def test_duplicate_reply_vote_is_rejected(self):
        ReplyVote.objects.create(
            reply=self.reply,
            user=self.voter,
            value=ReplyVote.Value.UP,
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                ReplyVote.objects.create(
                    reply=self.reply,
                    user=self.voter,
                    value=ReplyVote.Value.DOWN,
                )


class VoteViewTests(VoteModelTests):
    def test_vote_actions_on_threads_and_replies(self):
        from django.urls import reverse

        self.client.force_login(self.voter)

        cases = [
            ("forum:vote_thread", self.thread, ThreadVote, "thread"),
            ("forum:vote_reply", self.reply, ReplyVote, "reply"),
        ]

        for route, publication, model, relation in cases:
            with self.subTest(route=route):
                url = reverse(route, args=[publication.pk])
                lookup = {
                    relation: publication,
                    "user": self.voter,
                }

                # Crear un voto positivo.
                response = self.client.post(url, {"value": "1"})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(
                    response.json(),
                    {"score": 1, "user_vote": 1},
                )

                # Repetirlo no crea un voto duplicado.
                self.client.post(url, {"value": "1"})
                self.assertEqual(model.objects.filter(**lookup).count(), 1)

                # Cambiarlo por un voto negativo.
                response = self.client.post(url, {"value": "-1"})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(
                    response.json(),
                    {"score": -1, "user_vote": -1},
                )
                self.assertEqual(model.objects.filter(**lookup).count(), 1)

                # Retirar el voto.
                response = self.client.post(url, {"value": "0"})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(
                    response.json(),
                    {"score": 0, "user_vote": 0},
                )
                self.assertFalse(model.objects.filter(**lookup).exists())

    def test_vote_routes_require_login(self):
        from django.urls import reverse

        for route, publication in [
            ("forum:vote_thread", self.thread),
            ("forum:vote_reply", self.reply),
        ]:
            with self.subTest(route=route):
                response = self.client.post(
                    reverse(route, args=[publication.pk]),
                    {"value": "1"},
                )
                self.assertEqual(response.status_code, 302)

        self.assertFalse(ThreadVote.objects.exists())
        self.assertFalse(ReplyVote.objects.exists())

    def test_vote_routes_reject_get_and_invalid_values(self):
        from django.urls import reverse

        self.client.force_login(self.voter)

        for route, publication in [
            ("forum:vote_thread", self.thread),
            ("forum:vote_reply", self.reply),
        ]:
            with self.subTest(route=route):
                url = reverse(route, args=[publication.pk])

                self.assertEqual(self.client.get(url).status_code, 405)

                for value in ["2", "texto", ""]:
                    response = self.client.post(url, {"value": value})
                    self.assertEqual(response.status_code, 400)

        self.assertFalse(ThreadVote.objects.exists())
        self.assertFalse(ReplyVote.objects.exists())
