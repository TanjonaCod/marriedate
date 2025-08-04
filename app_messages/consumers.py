import json
from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from app_membres.models import Member
from .models import Message

class MessageNotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user_id = self.scope['session'].get('client', {}).get('id')
        if user_id:
            self.group_name = f"user_{user_id}"
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()
        else:
            await self.close()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def new_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'new_message',
            'message': event['message'],
            'count': event['count'],
        }))

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.room_group_name = f'chat_{self.user_id}'
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        content = data.get('content', '')
        image = data.get('image', None)
        sender_id = data['sender_id']
        receiver_id = data['receiver_id']

        # Sauvegarder le message en base
        sender = await sync_to_async(Member.objects.get)(id=sender_id)
        receiver = await sync_to_async(Member.objects.get)(id=receiver_id)
        message = await sync_to_async(Message.objects.create)(
            sender=sender,
            receiver=receiver,
            content=content,
            is_read=False
        )

        # Envoyer le message au groupe du destinataire
        await self.channel_layer.group_send(
            f'chat_{receiver_id}',
            {
                'type': 'chat_message',
                'message': content,
                'sender_id': sender_id,
                'receiver_id': receiver_id,
                'id': message.id,
                'timestamp': str(message.timestamp)
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'sender_id': event['sender_id'],
            'receiver_id': event['receiver_id'],
            'id': event.get('id'),
            'timestamp': event.get('timestamp')
        }))