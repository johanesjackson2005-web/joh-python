import json

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import ChatMessage
import redis
from django.conf import settings
from django.core.cache import cache
User = get_user_model()
redis_client = redis.from_url(
    settings.REDIS_URL,
    decode_responses=True
)

class ChatConsumer(AsyncWebsocketConsumer):
    @database_sync_to_async
    def set_user_online(self):

       user = self.scope["user"]

       if user.is_authenticated:

        key = f"user_online_{user.id}"


        count = redis_client.incr(key)


        # expire baada ya saa moja kama connection imekufa vibaya
        redis_client.expire(
            key,
            3600
        )


        # connection ya kwanza ndiyo inamfanya online
        if count == 1:

            profile = user.profile

            profile.is_online = True

            profile.save()

    @database_sync_to_async
    def set_user_offline(self):

      user = self.scope["user"]


      if user.is_authenticated:


        key = f"user_online_{user.id}"


        count = redis_client.decr(key)



        # hakuna connection tena
        if count <= 0:


            redis_client.delete(key)


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


# FIX PRIVATE ROOM ORDER
        if self.room_name.startswith("pm_"):

           parts = self.room_name.split("_")

           if len(parts) == 3:

              users = sorted([
              parts[1].lower(),
             parts[2].lower()
            ])

        self.room_name = f"pm_{users[0]}_{users[1]}"

        self.group_name = f'chat_{self.room_name}'
        print(
    "CONNECTED USER:",
    self.scope["user"].username,
    "ROOM:",
    self.room_name
)


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
                    "username",
                    ""
                    ).lower()

                    a = a.lower()
                    b = b.lower()

                    allowed = username in (a, b)

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
        await self.channel_layer.group_add(
    "online_users",
    self.channel_name
)
# Tuma messages 50 za mwisho wakati user anaingia
        if self.scope['user'].is_authenticated:

           await self.channel_layer.group_send(
                "online_users",
             {
            "type": "user_status",
            "username": self.scope["user"].username,
            "status": "online"
           }
              )
           if self.scope["user"].is_authenticated:

             await self.channel_layer.group_add(
             f"user_{self.scope['user'].id}",
              self.channel_name
    )
           print("JOINED:", f"user_{self.scope['user'].id}")

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
    "avatar": await self.get_user_avatar(msg.sender),
     
     }))
         
    async def disconnect(self, close_code):

    # Ondoa kwenye chat room
        if hasattr(self, "group_name"):

            await self.channel_layer.group_discard(
               self.group_name,
               self.channel_name
          )


    # Ondoa kwenye online users group
        await self.channel_layer.group_discard(
             "online_users",
            self.channel_name
        )
        
        user = self.scope.get("user")

        if user and user.is_authenticated:

            await self.channel_layer.group_discard(
        f"user_{user.id}",
        self.channel_name
          )


        if user and user.is_authenticated:

            # update database
           await self.set_user_offline()


        # waambie wengine user ameondoka
           await self.channel_layer.group_send(
            "online_users",
            {
                "type": "user_status",
                "username": user.username,
                "status": "offline"
            }
        )
    
    async def user_status(self, event):

     await self.send(
        text_data=json.dumps({
            "type": "user_status",
            "username": event["username"],
            "status": event["status"]
        })
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
    @database_sync_to_async
    def get_user_avatar(self, user):

        default = settings.STATIC_URL + "image/logo1.png"


        if not user:
           return default


        try:

            profile = user.profile


            if profile.avatar:

             return profile.avatar.url


            elif profile.avatar_choice:

             return (
                settings.STATIC_URL
                + "profile/"
                + profile.avatar_choice
            )


        except Exception as e:

         print("PROFILE ERROR:", e)


        return default
   
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
            "type": "chat_file",
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

                   await self.channel_layer.group_send(
                        self.group_name,
                {
                    "type": "chat_delete",
                    "message_id": message_id
                }
            )
                   await database_sync_to_async(msg.delete)()

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
        avatar = settings.STATIC_URL + "image/logo1.png"

        if sender_obj:

          try:

               profile = await database_sync_to_async(
                lambda: sender_obj.profile
                )()


               if profile.avatar:

                  avatar = profile.avatar.url


               elif profile.avatar_choice:

                   avatar = (
                settings.STATIC_URL +
                "profile/" +
                profile.avatar_choice
            )


          except Exception as e:

            print("AVATAR ERROR:", e)
        payload = {

    "type": "message",

    "id": saved_message.id,

    "message": message,

    "user": username,

    "avatar": avatar

     }

       # ==========================
# DM Notification
# ==========================
        print("===== DM START =====")
        print("ROOM:", self.room_name)
        print("SENDER:", sender_obj.username if sender_obj else None)
        if self.room_name.startswith("pm_") and sender_obj:

           try:

              parts = self.room_name.split("_", 2)

              user1 = await database_sync_to_async(
              User.objects.get
               )(username=parts[1])

              user2 = await database_sync_to_async(
              User.objects.get
               )(username=parts[2])

              receiver = user2 if sender_obj.username == user1.username else user1
              print("Trying notification...")

              parts = self.room_name.split("_", 2)
              print(parts)

              user1 = await database_sync_to_async(User.objects.get)(
              username=parts[1]
              )

              user2 = await database_sync_to_async(User.objects.get)(
              username=parts[2]
               )

              print("USER1:", user1.username)
              print("USER2:", user2.username)
              key = f"unread_{receiver.id}_{sender_obj.id}"

              count = await database_sync_to_async(
                  lambda: cache.incr(key) if cache.get(key) else cache.set(key,1,86400)
               )()


              await self.channel_layer.group_send(

                f"user_{receiver.id}",

      {
        "type": "dm_notification",

         "from": sender_obj.username,

             "sender_id": sender_obj.id,

                 "count": cache.get(key)

                   }

                 )

           except Exception as e:

              print("DM Notification Error:", e)

        await self.channel_layer.group_send(

           self.group_name,

          {

        "type": "chat.message",

        "text": json.dumps(payload)

    }
)   
    async def chat_message(self, event):

     await self.send(
        text_data=event["text"]
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
    async def dm_notification(self,event):

        await self.send(
                text_data=json.dumps({

            "type":"dm_notification",

            "from":event["from"],

            "sender_id":event["sender_id"],

            "count":event["count"]

        })
    )    