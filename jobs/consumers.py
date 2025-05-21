import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from .models import Job

class JobConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.job_id = self.scope['url_route']['kwargs']['job_id']
        self.job_group_name = f'job_{self.job_id}'

        # Join job group
        await self.channel_layer.group_add(
            self.job_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave job group
        await self.channel_layer.group_discard(
            self.job_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data=None, bytes_data=None):
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get('type')
        
        if message_type == 'status_update':
            # Handle status update from client
            status = text_data_json.get('status')
            await self.update_job_status(status)

    # Send message to group
    async def job_update(self, event):
        await self.send(text_data=json.dumps(event))

    @database_sync_to_async
    def update_job_status(self, status):
        job = Job.objects.filter(id=self.job_id).first()
        if job and job.status != status:
            job.status = status
            job.save()
            return True
        return False
