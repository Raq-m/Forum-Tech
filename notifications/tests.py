from django.contrib.auth import get_user_model
from django.test import TestCase

from chat.models import Conversation, Message
from config.celery import app as celery_app

from .models import Notification, NotificationType

User = get_user_model()


class ChatNotificationTests(TestCase):
    def setUp(self):
        celery_app.conf.task_always_eager = True
        self.addCleanup(setattr, celery_app.conf, "task_always_eager", False)

        self.carlos = User.objects.create_user(
            username="carlos", email="carlos@test.com", password="pwd12345"
        )
        self.cristina = User.objects.create_user(
            username="cristina", email="cristina@test.com", password="pwd12345"
        )
        self.conv = Conversation.objects.create(
            initiator=self.carlos, recipient=self.cristina
        )

    def test_mensaje_crea_notificacion_para_el_destinatario(self):
        Message.objects.create(
            conversation=self.conv, sender=self.carlos, text="Hola Cristina"
        )
        self.assertEqual(Notification.objects.filter(recipient=self.cristina).count(), 1)
        notificacion = Notification.objects.get(recipient=self.cristina)
        self.assertEqual(notificacion.notification_type, NotificationType.NEW_MESSAGE)
        self.assertFalse(notificacion.is_read)

    def test_el_remitente_no_recibe_notificacion(self):
        Message.objects.create(
            conversation=self.conv, sender=self.carlos, text="Hola Cristina"
        )
        self.assertEqual(Notification.objects.filter(recipient=self.carlos).count(), 0)