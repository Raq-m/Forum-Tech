from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Reply, Thread
from .validators import validate_forum_content


@override_settings(
    FORUM_BLOCKED_WORDS=["spamdemostracion"],
    FORUM_BLOCKED_DOMAINS=["spam.example"],
)
class ContentFilterTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="filter_user",
            email="filter@example.com",
        )
        self.thread = Thread.objects.create(
            author=self.user,
            title="Prueba de filtros",
            content="Contenido.",
        )
        self.client.force_login(self.user)
        self.url = reverse(
            "forum:reply_create",
            args=[self.thread.pk],
        )

    def test_blocked_word_ignores_case(self):
        with self.assertRaises(ValidationError):
            validate_forum_content("Texto SPAMDEMOSTRACION.")

    def test_word_inside_longer_word_is_allowed(self):
        validate_forum_content("antispamdemostracion")

    def test_blocked_domain_and_subdomains_are_rejected(self):
        for content in [
            "https://spam.example/oferta",
            "https://sub.spam.example/oferta",
            "www.spam.example",
            "https://SPAM.EXAMPLE/oferta",
        ]:
            with self.subTest(content=content):
                with self.assertRaises(ValidationError):
                    validate_forum_content(content)

    def test_similar_domain_is_not_blocked_by_suffix_alone(self):
        validate_forum_content("https://notspam.example")
        validate_forum_content("https://spam.example.org")

    def test_invalid_url_is_rejected(self):
        with self.assertRaises(ValidationError):
            validate_forum_content("https://[invalid")

    def test_rejected_content_is_not_saved(self):
        for content in [
            "spamdemostracion",
            "Mira https://spam.example",
        ]:
            with self.subTest(content=content):
                response = self.client.post(
                    self.url,
                    {"content": content},
                )

                self.assertEqual(response.status_code, 400)
                self.assertIn(
                    "content",
                    response.context["form"].errors,
                )

        self.assertFalse(Reply.objects.exists())

    def test_normal_reply_is_saved(self):
        response = self.client.post(
            self.url,
            {"content": "Consulta https://docs.djangoproject.com/"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Reply.objects.count(), 1)