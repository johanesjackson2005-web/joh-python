from django.db import models
from django.contrib.auth.models import User
from django.db import models
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