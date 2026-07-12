from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Profile
from .models import Notification

@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):

    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def welcome_notification(sender, instance, created, **kwargs):

    if created:

        Notification.objects.create(

            user=instance,

            title="Welcome to JMJ SOFTWARES",

            message="Karibu kwenye platform yetu."

        )