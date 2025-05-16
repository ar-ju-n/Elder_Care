import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from .models import Notification

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        if user.is_anonymous:
            await self.close()
        else:
            self.group_name = f"notifications_{user.id}"
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()

    async def disconnect(self, close_code):
        user = self.scope["user"]
        if not user.is_anonymous:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        if data.get("command") == "mark_all_read":
            await self.mark_all_read()

    @database_sync_to_async
    def mark_all_read(self):
        user = self.scope["user"]
        Notification.objects.filter(user=user, is_read=False).update(is_read=True)

    async def send_notification(self, event):
        await self.send(text_data=json.dumps(event["data"]))
