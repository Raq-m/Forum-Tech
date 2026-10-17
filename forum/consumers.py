from channels.generic.websocket import AsyncJsonWebsocketConsumer


class NotificationConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user = self.scope.get("user")

        if not user or not user.is_authenticated or not user.is_active:
            await self.close(code=4401)
            return

        self.group_name = f"notifications.user.{user.pk}"

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name,
        )
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name,
            )

    async def notification_created(self, event):
        await self.send_json({
            "type": "notification.created",
            "notification_id": event["notification_id"],
        })