from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Reply, Report, Thread


class ReportViewTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.author = User.objects.create_user(
            username="report_author",
            email="author@example.com",
        )
        self.reporter = User.objects.create_user(
            username="report_user",
            email="reporter@example.com",
        )
        self.thread = Thread.objects.create(
            author=self.author,
            title="Hilo de prueba",
            content="Contenido.",
        )
        self.reply = Reply.objects.create(
            thread=self.thread,
            author=self.author,
            content="Respuesta.",
        )

    def targets(self):
        return [
            ("forum:report_thread", self.thread, "thread"),
            ("forum:report_reply", self.reply, "reply"),
        ]

    def test_valid_reports_are_saved_once(self):
        self.client.force_login(self.reporter)

        for route, target, relation in self.targets():
            with self.subTest(route=route):
                url = reverse(route, args=[target.pk])
                data = {
                    "reason": Report.Reason.SPAM,
                    "description": "Publicidad repetida.",
                    "reporter": self.author.pk,
                    "status": Report.Status.REVIEWED,
                }

                response = self.client.post(url, data)

                self.assertRedirects(
                    response,
                    reverse(
                        "forum:thread_detail",
                        args=[self.thread.pk],
                    ),
                )

                lookup = {
                    "reporter": self.reporter,
                    relation: target,
                }
                report = Report.objects.get(**lookup)

                self.assertEqual(report.reason, Report.Reason.SPAM)
                self.assertEqual(report.status, Report.Status.PENDING)

                if relation == "thread":
                    self.assertIsNone(report.reply)
                else:
                    self.assertIsNone(report.thread)

                self.client.post(url, data)
                self.assertEqual(
                    Report.objects.filter(**lookup).count(),
                    1,
                )

                response = self.client.get(url)
                self.assertContains(
                    response,
                    "Ya has reportado esta publicación.",
                )

    def test_invalid_reason_is_rejected(self):
        self.client.force_login(self.reporter)

        for route, target, relation in self.targets():
            with self.subTest(route=route):
                response = self.client.post(
                    reverse(route, args=[target.pk]),
                    {"reason": "invalid"},
                )

                self.assertEqual(response.status_code, 200)
                self.assertIn(
                    "reason",
                    response.context["form"].errors,
                )

        self.assertFalse(Report.objects.exists())

    def test_get_does_not_create_reports(self):
        self.client.force_login(self.reporter)

        for route, target, relation in self.targets():
            response = self.client.get(
                reverse(route, args=[target.pk]),
            )
            self.assertEqual(response.status_code, 200)

        self.assertFalse(Report.objects.exists())

    def test_login_is_required(self):
        for route, target, relation in self.targets():
            url = reverse(route, args=[target.pk])

            self.assertEqual(
                self.client.get(url).status_code,
                302,
            )
            self.assertEqual(
                self.client.post(
                    url,
                    {"reason": Report.Reason.SPAM},
                ).status_code,
                302,
            )

        self.assertFalse(Report.objects.exists())