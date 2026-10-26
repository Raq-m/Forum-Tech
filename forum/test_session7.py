from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, close_old_connections, transaction
from django.test import TestCase, TransactionTestCase, skipUnlessDBFeature
from django.urls import reverse

from .models import Notification, Reply, ReplyVote, Tag, Thread, ThreadVote, UserFollow
from .search import hilos_visibles
from .services import archive_thread, merge_threads
from .solucion import aceptar_solucion
from .statistics import etiquetas_populares, hilos_populares, media_visitas_por_etiqueta, resumen_foro


class Session7Tests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = get_user_model().objects.create_user(username="author7", email="a7@example.com")
        cls.other = get_user_model().objects.create_user(username="other7", email="b7@example.com")
        cls.thread = Thread.objects.create(author=cls.author, title="Python", content="Texto")
        cls.reply = Reply.objects.create(author=cls.author, thread=cls.thread, content="Respuesta")

    def test_vote_values_are_enforced_by_database(self):
        for model, target in ((ThreadVote, {"thread": self.thread}), (ReplyVote, {"reply": self.reply})):
            for value in (0, 2, -2):
                with self.subTest(model=model, value=value):
                    with self.assertRaises(IntegrityError), transaction.atomic():
                        model.objects.create(user=self.other, value=value, **target)

    def test_unique_vote_and_follow(self):
        for model, fields in (
            (ThreadVote, dict(user=self.other, thread=self.thread, value=1)),
            (ReplyVote, dict(user=self.other, reply=self.reply, value=-1)),
            (UserFollow, dict(follower=self.other, followed=self.author)),
        ):
            model.objects.create(**fields)
            with self.assertRaises(IntegrityError), transaction.atomic():
                model.objects.create(**fields)

    def test_statistics_do_not_multiply_votes_by_replies_or_tags(self):
        Reply.objects.create(author=self.author, thread=self.thread, content="Otra")
        ThreadVote.objects.create(thread=self.thread, user=self.author, value=1)
        ThreadVote.objects.create(thread=self.thread, user=self.other, value=-1)
        self.thread.tags.set(Tag.desde_texto("python django"))
        Thread.objects.filter(pk=self.thread.pk).update(views_count=4)
        Thread.objects.create(author=self.author, title="Oculto", content="x", is_deleted=True)
        result = resumen_foro()
        self.assertEqual(result["total"], 1)
        self.assertEqual(result["media_respuestas"], 2)
        self.assertEqual(result["maximo_visitas"], 4)
        self.assertEqual(hilos_visibles().get().puntuacion, 0)
        self.assertEqual([tag.num_hilos for tag in etiquetas_populares()], [1, 1])
        self.assertEqual([row["media_visitas"] for row in media_visitas_por_etiqueta()], [4, 4])

    def test_authors_and_tags_use_two_queries_for_many_threads(self):
        for n in range(4):
            hilo = Thread.objects.create(author=self.author, title=f"Hilo {n}", content="x")
            hilo.tags.set(Tag.desde_texto("python"))
        with self.assertNumQueries(2):
            for hilo in hilos_visibles().prefetch_related("tags"):
                str(hilo.author)
                list(hilo.tags.all())

    def test_popular_tags_limit_and_counts_ignore_hidden_threads(self):
        tags = [Tag.objects.create(name=f"tag{n}") for n in range(6)]
        for n, tag in enumerate(tags):
            for i in range(n + 1):
                hilo = Thread.objects.create(author=self.author, title=f"{n}-{i}", content="x")
                hilo.tags.add(tag)
        for fields in ({"is_deleted": True}, {"merged_into": self.thread}):
            hidden = Thread.objects.create(author=self.author, title="Oculto", content="x", **fields)
            hidden.tags.add(tags[0])
        self.assertEqual(
            [(tag.name, tag.num_hilos) for tag in etiquetas_populares()],
            [(f"tag{n}", n + 1) for n in range(5, 0, -1)],
        )

    def test_popular_threads_top_ten_excludes_hidden_and_keeps_scores(self):
        threads = [Thread.objects.create(author=self.author, title=f"Popular {n}", content="x") for n in range(12)]
        for hilo in threads:
            ThreadVote.objects.create(thread=hilo, user=self.other, value=1)
        winner = threads[0]
        ThreadVote.objects.create(thread=winner, user=self.author, value=1)
        winner.tags.set(Tag.desde_texto("python django"))
        for n in range(3):
            Reply.objects.create(thread=winner, author=self.author, content=f"Respuesta {n}")
        for fields in ({"is_deleted": True}, {"merged_into": self.thread}):
            hidden = Thread.objects.create(author=self.author, title="Oculto", content="x", **fields)
            ThreadVote.objects.create(thread=hidden, user=self.other, value=1)
        result = list(hilos_populares())
        self.assertEqual(len(result), 10)
        self.assertEqual(result[0].pk, winner.pk)
        self.assertEqual(result[0].puntuacion, 2)
        self.assertEqual(result[0].num_respuestas, 3)
        self.assertTrue(set(h.pk for h in result).issubset({h.pk for h in threads}))

    def test_tag_average_uses_only_visible_threads_and_empty_groups_are_null(self):
        tag, empty = Tag.desde_texto("python vacia")
        self.thread.tags.add(tag)
        Thread.objects.filter(pk=self.thread.pk).update(views_count=2)
        visible = Thread.objects.create(author=self.author, title="Visible", content="x", views_count=8)
        visible.tags.add(tag)
        for fields in ({"is_deleted": True}, {"merged_into": self.thread}):
            hidden = Thread.objects.create(author=self.author, title="Oculto", content="x", views_count=100, **fields)
            hidden.tags.add(tag)
        Reply.objects.create(thread=self.thread, author=self.author, content="Eliminada", is_deleted=True)
        averages = {row["name"]: row["media_visitas"] for row in media_visitas_por_etiqueta()}
        self.assertEqual(averages[tag.name], 5)
        self.assertIsNone(averages[empty.name])
        self.assertEqual(resumen_foro(), {
            "total": 2, "media_respuestas": 0.5, "minimo_visitas": 2, "maximo_visitas": 8,
        })

    def test_detail_increments_visits_and_merged_url_does_not(self):
        url = reverse("forum:thread_detail", args=[self.thread.pk])
        self.assertEqual(self.client.get(url).status_code, 200)
        self.assertEqual(self.client.get(url).status_code, 200)
        self.thread.refresh_from_db()
        self.assertEqual(self.thread.views_count, 2)
        target = Thread.objects.create(author=self.author, title="Destino", content="x")
        merge_threads(self.thread.pk, target.pk)
        self.assertEqual(self.client.get(url).status_code, 302)
        self.thread.refresh_from_db()
        self.assertEqual(self.thread.views_count, 2)

    def test_archive_requires_owner_and_rejects_second_archive(self):
        with self.assertRaises(PermissionDenied):
            archive_thread(self.thread.pk, self.other)
        archive_thread(self.thread.pk, self.author)
        self.assertFalse(hilos_visibles().filter(pk=self.thread.pk).exists())
        with self.assertRaises(ValidationError):
            archive_thread(self.thread.pk, self.author)

    def test_solution_rechecks_stale_reply_after_merge(self):
        target = Thread.objects.create(author=self.author, title="Destino", content="x")
        aceptar_solucion(self.thread, self.reply, self.author)
        merge_threads(self.thread.pk, target.pk)
        with self.assertRaises(ValidationError):
            aceptar_solucion(self.thread, self.reply, self.author)
        self.thread.refresh_from_db()
        self.assertIsNone(self.thread.accepted_reply_id)

    def test_merge_rolls_back_moved_replies_and_notifications_on_failure(self):
        target = Thread.objects.create(author=self.author, title="Destino", content="x")
        notice = Notification.objects.create(recipient=self.other, actor=self.author,
                                            thread=self.thread, reply=self.reply, kind="reply")
        with patch.object(Thread, "save", side_effect=RuntimeError("fallo simulado")):
            with self.assertRaises(RuntimeError):
                merge_threads(self.thread.pk, target.pk)
        self.reply.refresh_from_db()
        notice.refresh_from_db()
        self.thread.refresh_from_db()
        self.assertEqual(self.reply.thread_id, self.thread.pk)
        self.assertEqual(notice.thread_id, self.thread.pk)
        self.assertIsNone(self.thread.merged_into_id)


class PostgreSQLConcurrencyTests(TransactionTestCase):
    @skipUnlessDBFeature("has_select_for_update")
    def test_only_one_concurrent_merge_can_move_source(self):
        author = get_user_model().objects.create_user(username="parallel7", email="parallel7@example.com")
        source, a, b = [Thread.objects.create(author=author, title=t, content="x") for t in ("Origen", "A", "B")]
        reply = Reply.objects.create(author=author, thread=source, content="x")
        barrier = Barrier(2)

        def merge(target_id):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                try:
                    merge_threads(source.pk, target_id)
                    return True
                except ValidationError:
                    return False
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(merge, [a.pk, b.pk]))
        self.assertEqual(sorted(results), [False, True])
        source.refresh_from_db()
        reply.refresh_from_db()
        self.assertEqual(reply.thread_id, source.merged_into_id)
