from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile
class Background(models.Model):
    title = models.CharField(max_length=100)
    image = models.ImageField(upload_to='backgrounds/')
    def __str__(self):
        return self.title
    
class PasswordResetOTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.user.username} - {self.otp}"
class Setup(models.Model):
    name = models.CharField(max_length=100)
    download_url = models.URLField()
class Contact(models.Model):
    username = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    admin_reply = models.TextField(blank=True, null=True)
    
   

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="categories/", blank=True, null=True)

    def __str__(self):
        return self.name


class Software(models.Model):
    
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    version = models.CharField(max_length=30, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="software/", blank=True, null=True)
    download_link = models.URLField()
    size = models.CharField(max_length=30, blank=True)

    def __str__(self):
        return self.name
class Tutorial(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="tutorials"
    )

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    thumbnail = models.ImageField(upload_to="tutorials/", blank=True, null=True)
    youtube_link = models.URLField(blank=True)
    video_file = models.FileField(upload_to="tutorials/videos/", blank=True, null=True)

    instructor = models.CharField(max_length=100, blank=True)
    duration = models.CharField(max_length=30, blank=True)

    featured = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
    def get_embed_url(self):

      url = self.youtube_link


      if "youtube.com/watch?v=" in url:

        video_id = url.split("watch?v=")[1].split("&")[0]

        return f"https://www.youtube.com/embed/{video_id}"


      elif "youtu.be/" in url:

        video_id = url.split("youtu.be/")[1].split("?")[0]

        return f"https://www.youtube.com/embed/{video_id}"


      elif "youtube.com/embed/" in url:

        return url


      return None
    
from django.utils import timezone

class LiveStream(models.Model):

    STATUS_CHOICES = [
        ("LIVE", "Live"),
        ("UPCOMING", "Upcoming"),
        ("ENDED", "Ended"),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    thumbnail = models.ImageField(
        upload_to="livestreams/",
        blank=True,
        null=True
    )

    youtube_live = models.URLField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="UPCOMING"
    )

    start_time = models.DateTimeField(
        default=timezone.now
    )

    created_at = models.DateTimeField(auto_now_add=True)
    def get_embed_url(self):

     url = self.youtube_live


     if "youtube.com/watch?v=" in url:

        video_id = url.split("watch?v=")[1].split("&")[0]

        return f"https://www.youtube.com/embed/{video_id}"


     elif "youtu.be/" in url:

        video_id = url.split("youtu.be/")[1].split("?")[0]

        return f"https://www.youtube.com/embed/{video_id}"


     elif "youtube.com/embed/" in url:

        return url


     return None
    def __str__(self):
        return self.title
    



class Profile(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    avatar = models.CharField(
        max_length=100,
        default="default.jpg"
    )

    last_seen = models.DateTimeField(
        null=True,
        blank=True
    )

    is_online = models.BooleanField(
        default=False
    )
    def __str__(self):
        return self.user.username

class ChatMessage(models.Model):

    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    guest_name = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )

    room = models.CharField(max_length=100)

    message = models.TextField(
        blank=True,
        null=True
    )

    file = models.FileField(
        upload_to="chat/uploads/",
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    deleted_by = models.ManyToManyField(
        User,
        related_name="deleted_messages",
        blank=True
    )
class Conversation(models.Model):

    user1 = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="conversation_user1"
    )

    user2 = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="conversation_user2"
    )

    last_message = models.ForeignKey(
        ChatMessage,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )


    def __str__(self):
        return f"{self.user1} - {self.user2}"


    class Meta:
      ordering = ['-updated_at']
class ChatMemory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10)  # "user" or "ai"
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.role}"


class Notification(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notifications"
    )

    title = models.CharField(
        max_length=200
    )

    message = models.TextField()

    is_read = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )


    def __str__(self):
        return f"{self.user.username} - {self.title}"
 
class Movie(models.Model):

    CATEGORY_CHOICES = (

        ("Action","Action"),
        ("Comedy","Comedy"),
        ("Horror","Horror"),
        ("Animation","Animation"),
        ("Sci-Fi","Sci-Fi"),
        ("Drama","Drama"),

    )


    title = models.CharField(
        max_length=200
    )


    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES
    )


    poster = models.ImageField(
        upload_to="movies/"
    )


    year = models.CharField(
        max_length=10
    )


    duration = models.CharField(
        max_length=50
    )

    embed_link = models.URLField(
    blank=True,
    null=True
)
    watch_link = models.URLField()



    created_at = models.DateTimeField(
        auto_now_add=True
    )



    def __str__(self):

        return self.title
    def save(self, *args, **kwargs):

      super().save(*args, **kwargs)


      if self.poster:

         img = Image.open(
            self.poster.path
        )


         max_size = (600,900)


         img.thumbnail(
            max_size
        )


         img.save(
            self.poster.path,
            quality=85,
            optimize=True
        )
    def get_embed_url(self):

       url = self.watch_link


       if "youtube.com/watch?v=" in url:

        video_id = url.split("v=")[1]

        return f"https://www.youtube.com/embed/{video_id}"


       elif "youtu.be/" in url:

        video_id = url.split("/")[-1]

        return f"https://www.youtube.com/embed/{video_id}"


       else:

        return None
class Game(models.Model):

    GAME_TYPE = (

        ("ONLINE","Online Game"),
        ("OFFLINE","Offline Game"),

    )


    PLATFORM = (

        ("PC","PC"),
        ("ANDROID","Android"),
        ("WEB","Web"),

    )


    title = models.CharField(
        max_length=200
    )


    description = models.TextField(
        blank=True
    )


    image = models.ImageField(
        upload_to="games/"
    )


    game_type = models.CharField(
        max_length=20,
        choices=GAME_TYPE
    )


    platform = models.CharField(
        max_length=20,
        choices=PLATFORM
    )


    size = models.CharField(
        max_length=50,
        blank=True
    )


    play_link = models.URLField(
        blank=True
    )


    embed_link = models.URLField(
        blank=True,
        null=True
    )


    created_at = models.DateTimeField(
        auto_now_add=True
    )


    def __str__(self):

        return self.title



    def get_embed_url(self):

        return self.embed_link
class OnlineGame(models.Model):

    title = models.CharField(
        max_length=200
    )

    description = models.TextField(
        blank=True
    )


    thumbnail = models.ImageField(
        upload_to="online_games/",
        blank=True,
        null=True
    )


    game_link = models.URLField()


    embed_link = models.URLField(
        blank=True,
        null=True
    )


    category = models.CharField(
        max_length=100,
        default="Action"
    )


    created_at = models.DateTimeField(
        auto_now_add=True
    )


    def get_embed_url(self):

        url = self.embed_link


        if url:
            return url

        return None


    def __str__(self):

        return self.title



class OfflineGame(models.Model):

    title = models.CharField(
        max_length=200
    )


    description = models.TextField(
        blank=True
    )


    thumbnail = models.ImageField(
        upload_to="offline_games/",
        blank=True,
        null=True
    )


    download_link = models.URLField()


    size = models.CharField(
        max_length=50,
        blank=True
    )


    version = models.CharField(
        max_length=50,
        blank=True
    )


    created_at = models.DateTimeField(
        auto_now_add=True
    )


    def __str__(self):

        return self.title