import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import ChatRequest, ChatMessage
from django.urls import reverse

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.request_id = self.scope['url_route']['kwargs']['request_id']
        self.room_group_name = f'chat_{self.request_id}'

        # Get the chat request
        chat_request = await self.get_chat_request(self.request_id)
        user = self.scope['user']
        
        # Only allow participants to connect
        if user.is_authenticated and (user.id == chat_request.elder_id or user.id == chat_request.caregiver_id):
            # Join room group
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            await self.accept()
        else:
            # Reject the connection
            await self.close()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        data = json.loads(text_data)
        user = self.scope['user']
        
        # Handle typing indicator
        if data.get('type') == 'typing':
            # Send typing indicator to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'typing_indicator',
                    'username': user.username,
                    'user_id': user.id
                }
            )
            return
        
        # Handle file upload notification
        if data.get('type') == 'file_uploaded':
            message_id = data.get('message_id')
            if message_id:
                message = await self.get_message(message_id)
                if message:
                    # Send file notification to room group
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            'type': 'file_message',
                            'message': message.message,
                            'username': user.username,
                            'user_id': user.id,
                            'timestamp': message.timestamp.isoformat(),
                            'message_id': message.id,
                            'attachment_url': message.attachment.url if message.attachment else None,
                            'attachment_name': message.attachment_name,
                            'is_image': message.is_image,
                            'file_size': message.file_size_display
                        }
                    )
                    
                    # Send notification to other user
                    chat_request = await self.get_chat_request(self.request_id)
                    other_user_id = chat_request.elder_id if user.id == chat_request.caregiver_id else chat_request.caregiver_id
                    
                    # Send to notification consumer
                    channel_layer = get_channel_layer()
                    await channel_layer.group_send(
                        f'notifications_{other_user_id}',
                        {
                            'type': 'notification_message',
                            'event': 'new_message',
                            'sender_name': user.username,
                            'message_preview': f"{user.username} sent a file: {message.attachment_name}",
                            'chat_url': f"/chat/room/{self.request_id}/"
                        }
                    )
            return
            
        # Handle chat message
        message = data.get('message', '').strip()
        if not message:
            return
            
        # Save message to database
        msg = await self.save_message(self.request_id, user.id, message)
        
        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'username': user.username,
                'user_id': user.id,
                'timestamp': msg.timestamp.isoformat(),
                'message_id': msg.id
            }
        )
        
        # Send notification to other user
        chat_request = await self.get_chat_request(self.request_id)
        other_user_id = chat_request.elder_id if user.id == chat_request.caregiver_id else chat_request.caregiver_id
        
        # Send to notification consumer
        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            f'notifications_{other_user_id}',
            {
                'type': 'notification_message',
                'event': 'new_message',
                'sender_name': user.username,
                'message_preview': message[:50] + ('...' if len(message) > 50 else ''),
                'chat_url': f"/chat/room/{self.request_id}/"
            }
        )

    # Receive message from room group
    async def chat_message(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message'],
            'username': event['username'],
            'user_id': event['user_id'],
            'timestamp': event['timestamp'],
            'message_id': event['message_id']
        }))
    
    # Send file message to WebSocket
    async def file_message(self, event):
        # Send file message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'file_message',
            'message': event['message'],
            'username': event['username'],
            'user_id': event['user_id'],
            'timestamp': event['timestamp'],
            'message_id': event['message_id'],
            'attachment_url': event['attachment_url'],
            'attachment_name': event['attachment_name'],
            'is_image': event['is_image'],
            'file_size': event['file_size']
        }))
    
    # Send typing indicator to WebSocket
    async def typing_indicator(self, event):
        await self.send(text_data=json.dumps({
            'type': 'typing',
            'username': event['username'],
            'user_id': event['user_id']
        }))
    
    @database_sync_to_async
    def get_chat_request(self, request_id):
        from .models import ChatRequest
        return ChatRequest.objects.get(id=request_id)
    
    @database_sync_to_async
    def get_message(self, message_id):
        from .models import ChatMessage
        try:
            return ChatMessage.objects.get(id=message_id)
        except ChatMessage.DoesNotExist:
            return None
    
    @database_sync_to_async
    def save_message(self, request_id, user_id, message):
        from .models import ChatMessage, ChatRequest
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        chat_request = ChatRequest.objects.get(id=request_id)
        user = User.objects.get(id=user_id)
        
        msg = ChatMessage.objects.create(
            chat_request=chat_request,
            sender=user,
            message=message
        )
        return msg

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.notification_group_name = f'notifications_{self.user_id}'
        
        # Join notification group
        await self.channel_layer.group_add(
            self.notification_group_name,
            self.channel_name
        )
        
        await self.accept()

    async def disconnect(self, close_code):
        # Leave notification group
        await self.channel_layer.group_discard(
            self.notification_group_name,
            self.channel_name
        )

    # Receive message from notification group
    async def notification_message(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps(event))






