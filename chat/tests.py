from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase
from django.urls import reverse

from .services import get_or_create_conversation, mark_messages_as_read, send_message

User = get_user_model()


class ChatServiceTests(TestCase):
    def setUp(self):
        self.ana = User.objects.create_user(
            username="ana", email="ana@example.com", password="Password123!"
        )
        self.luis = User.objects.create_user(
            username="luis", email="luis@example.com", password="Password123!"
        )
        self.intruso = User.objects.create_user(
            username="intruso", email="intruso@example.com", password="Password123!"
        )

    def test_cannot_chat_with_yourself(self):
        with self.assertRaises(ValidationError):
            get_or_create_conversation(self.ana, self.ana.pk)

    def test_conversation_is_reused_in_both_directions(self):
        conv1 = get_or_create_conversation(self.ana, self.luis.pk)
        conv2 = get_or_create_conversation(self.luis, self.ana.pk)
        self.assertEqual(conv1.pk, conv2.pk)

    def test_send_message(self):
        conv = get_or_create_conversation(self.ana, self.luis.pk)
        msg = send_message(self.ana, conv.pk, "Hola Luis")
        self.assertEqual(msg.sender, self.ana)
        self.assertFalse(msg.is_read)

    def test_empty_message_is_rejected(self):
        conv = get_or_create_conversation(self.ana, self.luis.pk)
        with self.assertRaises(ValidationError):
            send_message(self.ana, conv.pk, "   ")

    def test_intruder_cannot_send_message(self):
        conv = get_or_create_conversation(self.ana, self.luis.pk)
        with self.assertRaises(PermissionDenied):
            send_message(self.intruso, conv.pk, "Me cuelo")

    def test_messages_are_marked_as_read(self):
        conv = get_or_create_conversation(self.ana, self.luis.pk)
        msg = send_message(self.ana, conv.pk, "Hola")
        mark_messages_as_read(conv.pk, self.luis)
        msg.refresh_from_db()
        self.assertTrue(msg.is_read)


class ChatViewTests(TestCase):
    def setUp(self):
        self.ana = User.objects.create_user(
            username="ana", email="ana@example.com", password="Password123!"
        )
        self.luis = User.objects.create_user(
            username="luis", email="luis@example.com", password="Password123!"
        )
        self.intruso = User.objects.create_user(
            username="intruso", email="intruso@example.com", password="Password123!"
        )
        self.conv = get_or_create_conversation(self.ana, self.luis.pk)

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(reverse("chat:inbox"))
        self.assertEqual(response.status_code, 302)

    def test_intruder_cannot_open_conversation(self):
        self.client.login(username="intruso", password="Password123!")
        response = self.client.get(reverse("chat:detail", args=[self.conv.pk]))
        self.assertEqual(response.status_code, 403)