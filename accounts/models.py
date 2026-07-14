from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

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


    watch_link = models.URLField()



    created_at = models.DateTimeField(
        auto_now_add=True
    )



    def __str__(self):

        return self.title