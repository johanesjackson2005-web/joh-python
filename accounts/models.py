from django.db import models
from django.contrib.auth.models import User
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