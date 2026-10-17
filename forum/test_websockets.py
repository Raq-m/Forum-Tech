from types import SimpleNamespace

from channels.layers import get_channel_layer
from channels.testing import WebsocketCommunicator
from django.test import SimpleTestCase, override_settings

from .consumers import NotificationConsumer


@override_settings(
    CHANNEL_LAYERS={
        "default": {
            "BACKEND": "channels.layers.InMemoryChannelLayer",
        },
    },
)
class NotificationWebSocketTests(SimpleTestCase):
    def communicator(self, user):
        communicator = WebsocketCommunicator(
            NotificationConsumer.as_asgi(),
            "/ws/notifications/",
        )
        communicator.scope["user"] = user
        return communicator

    async def test_anonymous_connection_is_rejected(self):
        connection = self.communicator(
            SimpleNamespace(is_authenticated=False),
        )

        try:
            connected, code = await connection.connect()
            self.assertFalse(connected)
            self.assertEqual(code, 4401)
        finally:
            await connection.disconnect()

    async def test_inactive_user_is_rejected(self):
        connection = self.communicator(
            SimpleNamespace(
                pk=1,
                is_authenticated=True,
                is_active=False,
            ),
        )

        try:
            connected, code = await connection.connect()
            self.assertFalse(connected)
            self.assertEqual(code, 4401)
        finally:
            await connection.disconnect()

    async def test_notification_reaches_only_its_recipient(self):
        first = self.communicator(
            SimpleNamespace(
                pk=101,
                is_authenticated=True,
                is_active=True,
            ),
        )
        second = self.communicator(
            SimpleNamespace(
                pk=202,
                is_authenticated=True,
                is_active=True,
            ),
        )

        try:
            first_connected, _ = await first.connect()
            second_connected, _ = await second.connect()
            self.assertTrue(first_connected)
            self.assertTrue(second_connected)

            await get_channel_layer().group_send(
                "notifications.user.101",
                {
                    "type": "notification.created",
                    "notification_id": 123,
                },
            )

            message = await first.receive_json_from()

            self.assertEqual(
                message,
                {
                    "type": "notification.created",
                    "notification_id": 123,
                },
            )
            self.assertTrue(
                await second.receive_nothing(timeout=0.1),
            )
        finally:
            await first.disconnect()
            await second.disconnect()