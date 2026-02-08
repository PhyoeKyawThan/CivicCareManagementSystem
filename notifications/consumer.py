import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']

        if self.user.is_anonymous:
            await self.close()

        else:
            self.group_name = f"user_{self.user.id}"

            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )
            await self.accept()
    async def disconnect(self, code):
        if not self.user.is_anonymous:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def send_notification(self, event):
        await self.send(text_data=json.dumps({
            "notification": event['notification']
        }))
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')

        if action == 'mark_as_read':
            notification_id = data.get('notification_id')
            await self.mark_notification_as_read(notification_id)

    @database_sync_to_async
    def mark_notification_as_read(self, notification_id):
        from notifications.models import Notification
        from django.utils import timezone

        if notification_id == 'all':
            Notification.objects.filter(user=self.scope['user'], is_read=False).update(
                is_read=True, read_at=timezone.now()
            )
        else:
            Notification.objects.filter(id=notification_id, user=self.scope['user']).update(
                is_read=True, read_at=timezone.now()
            )