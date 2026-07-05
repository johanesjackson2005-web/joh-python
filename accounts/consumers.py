import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import AnonymousUser
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import ChatMessage

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # room name provided in URL route kwargs: e.g. ws://.../ws/chat/<room_name>/
        self.room_name = self.scope['url_route']['kwargs'].get('room_name', 'global')
        self.group_name = f'chat_{self.room_name}'

        # Access control: if trying to join a user-specific room, ensure user owns it or is staff
        allowed = True
        if self.room_name.startswith('user_'):
            try:
                uid = int(self.room_name.split('_', 1)[1])
            except Exception:
                uid = None

            user = self.scope.get('user', None)
            if not user or not user.is_authenticated:
                allowed = False
            else:
                if user.is_staff:
                    allowed = True
                else:
                    allowed = (user.id == uid)

        # Private (peer-to-peer) rooms: format 'pm_<name1>_<name2>' where either participant may join
        elif self.room_name.startswith('pm_'):
            try:
                parts = self.room_name.split('_', 2)
                a = parts[1]
                b = parts[2]
            except Exception:
                a = b = None

            user = self.scope.get('user', None)
            if not user or not user.is_authenticated:
                allowed = False
            else:
                if user.is_staff:
                    allowed = True
                else:
                    uname = getattr(user, 'username', '')
                    allowed = (uname == a or uname == b)

        if not allowed:
            await self.close()
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        if text_data is None:
            return
        data = json.loads(text_data)
        message = data.get('message')

        user = self.scope.get('user', None)
        username = None
        sender_obj = None
        if user and getattr(user, 'is_authenticated', False):
            username = user.username
            sender_obj = user
        else:
            username = data.get('username', 'Anonymous')

        payload = {
            'message': message,
            'user': username,
        }

        # persist message
        try:
            await database_sync_to_async(ChatMessage.objects.create)(
                sender=sender_obj,
                room=self.room_name,
                message=message
            )
        except Exception:
            # ignore persistence errors
            pass

        # Broadcast to group
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'chat.message',
                'text': json.dumps(payload)
            }
        )

    async def chat_message(self, event):
        # forward message to WebSocket
        await self.send(text_data=event['text'])
