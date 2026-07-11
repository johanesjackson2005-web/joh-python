import json

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import ChatMessage


User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    @database_sync_to_async
    def set_user_online(self):

     user = self.scope["user"]

     if user.is_authenticated:

        profile = user.profile

        profile.is_online = True
        profile.save()



    @database_sync_to_async
    def set_user_offline(self):

     user = self.scope["user"]

     if user.is_authenticated:

        profile = user.profile

        profile.is_online = False
        profile.last_seen = timezone.now()
        profile.save()
    async def connect(self):

        # Room name from URL
        self.room_name = self.scope['url_route']['kwargs'].get(
            'room_name',
            'global'
        )

        self.group_name = f'chat_{self.room_name}'


        # ===============================
        # ACCESS CONTROL
        # ===============================

        allowed = True


        # User private room
        if self.room_name.startswith('user_'):

            try:
                uid = int(self.room_name.split('_', 1)[1])
            except Exception:
                uid = None


            user = self.scope.get('user')


            if not user or not user.is_authenticated:
                allowed = False

            else:
                if user.is_staff:
                    allowed = True
                else:
                    allowed = (user.id == uid)



        # Private user-to-user room
        elif self.room_name.startswith('pm_'):

            try:
                parts = self.room_name.split('_', 2)

                a = parts[1]
                b = parts[2]

            except Exception:

                a = None
                b = None


            user = self.scope.get('user')


            if not user or not user.is_authenticated:
                allowed = False

            else:

                if user.is_staff:

                    allowed = True

                else:

                    username = getattr(
                        user,
                        'username',
                        ''
                    )

                    allowed = (
                        username == a or
                        username == b
                    )


        if not allowed:

            await self.close()
            return


        await self.channel_layer.group_add(
        self.group_name,
         self.channel_name
) 
        await self.accept()

# SET USER ONLINE
        await self.set_user_online()

        print(
    "CHAT CONNECTED:",
    self.room_name,
    self.scope.get("user")
)

# Tuma messages 50 za mwisho wakati user anaingia
        if self.scope['user'].is_authenticated:
            user_id = self.scope['user'].id
        else:
            user_id = None

        messages = await self.get_last_messages(user_id)

        for msg in messages:
         await self.send(text_data=json.dumps({
           "type": "message",
           "id": msg.id,
           "user": (
          msg.sender.username
        if msg.sender
        else msg.guest_name
      ),
    "message": msg.message,
     "avatar" : "/static/profile/" + str(msg.sender.profile.avatar
    if msg.sender and hasattr(msg.sender, "profile") and msg.sender.profile.avatar
    else "/static/image/logo1.png"),
     }))
         

    async def disconnect(self, close_code):

       await self.set_user_offline()

       if hasattr(self, "group_name"):

        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
        
    @database_sync_to_async
    def get_last_messages(self, user_id):

        messages = ChatMessage.objects.filter(
            room=self.room_name
    )

        if user_id:
           messages = messages.exclude(
            deleted_by__id=user_id
        )

        messages = messages.select_related(
        "sender",
        "sender__profile"
    ).order_by("-created_at")[:50]


        return reversed(list(messages))

   
    # =====================================
    # RECEIVE MESSAGE
    # =====================================

    async def receive(
        self,
        text_data=None,
        bytes_data=None
    ):
        


        if text_data is None:
            return



        data = json.loads(text_data)



        event_type = data.get(
            "type",
            "message"
        )
         
        if event_type == "file":

           user = self.scope.get("user")

    # SAVE FILE MESSAGE IN DATABASE
           saved_file = await database_sync_to_async(
           ChatMessage.objects.create
         )(
          sender=user if user.is_authenticated else None,
          guest_name=None if user.is_authenticated else "Guest",
           room=self.room_name,
          message=data["url"]
          )


           await self.channel_layer.group_send(
             self.group_name,
           {
            "type": "chat.file",
            "id": saved_file.id,
            "url": data["url"],
            "name": data["name"]
          }
      )

           return

             

        # =================================
        # DELETE MESSAGE EVENT
        # =================================
        
        if event_type == "delete":

            message_id = data.get("message_id")
            user = self.scope.get("user")

            if not user or not user.is_authenticated:
                return

            try:

                msg = await database_sync_to_async(
                 ChatMessage.objects.select_related("sender").get
                  )(id=message_id)

        # ==========================================
        # SENDER (au Admin) => Delete for everyone
        # ==========================================
                if msg.sender == user or user.is_staff:

                   await database_sync_to_async(msg.delete)()

                   await self.channel_layer.group_send(
                        self.group_name,
                {
                    "type": "chat.delete",
                    "message_id": message_id
                }
            )

        # ==========================================
        # RECEIVER => Delete for me only
        # ==========================================
                else:

                 await database_sync_to_async(
                  msg.deleted_by.add
                  )(user)

                 await self.send(
                text_data=json.dumps({
                    "type": "delete",
                    "message_id": message_id
                })
            )

            except ChatMessage.DoesNotExist:

             print("Message not found")

            except Exception as e:

             print("DELETE ERROR:", e)

            return
       


         

          

        # =================================
        # NORMAL MESSAGE EVENT
        # =================================


        message = data.get(
           "message",
         ""
        )


        message_id = data.get(
      "id"
      )


        user = self.scope.get(
        'user'
     )


        sender_obj = None


        if user and user.is_authenticated:

           username = user.username
           sender_obj = user

        else:

            username = data.get(
             "username",
            "Guest"
       )

            sender_obj = None


        try:

          saved_message = await database_sync_to_async(
           ChatMessage.objects.create
    )(
          sender=sender_obj,
          guest_name=None if sender_obj else username,
          room=self.room_name,
          message=message,
          
    )

          print("MESSAGE SAVED:", saved_message.id)

        except Exception as e:

           print("SAVE ERROR:", e)
           return



# PROFILE IMAGE
        avatar = "/static/image/logo1.png"

        if sender_obj:
         try:
              if sender_obj.profile.avatar:
                 avatar = "/static/profile/" + str(sender_obj.profile.avatar)
         except Exception:
             pass
        payload = {

    "type": "message",

    "id": saved_message.id,

    "message": message,

    "user": username,

    "avatar": avatar

     }



        await self.channel_layer.group_send(

           self.group_name,

          {

        "type": "chat.message",

        "text": json.dumps(payload)

    }
)
    async def chat_delete(self, event):

     await self.send(
        text_data=json.dumps({
            "type": "delete",
            "message_id": event["message_id"]
        })
 )   
    async def chat_file(self,event):

      await self.send(
        text_data=json.dumps({

            "type":"file",
            "id":event["id"],

            "url":event["url"],

            "name":event["name"]

        })
    )     