from .models import Notification
from .models import Movie
from django.contrib import admin
from .models import Profile
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from .models import Contact
from .models import Category, Software,Tutorial, LiveStream
from .models import ChatMessage
admin.site.site_header = "JOHBOY SETUPS ADMIN"
admin.site.site_title = "JOHBOY SETUPS"
admin.site.index_title = "Welcome to JOHBOY SETUPS Dashboard"   
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = (
        'username',
        'email',
        'created_at'
    )

    fields = (
        'username',
        'email',
        'message',
        'admin_reply'
    )
@admin.register(Tutorial)
class TutorialAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "category",
        "instructor",
        "featured",
        "created_at",
        
    )

    list_filter = (
        "category",
        "featured",
    )

    search_fields = (
        "title",
        
    )


admin.site.register(Category)
admin.site.register(Software)
admin.site.register(LiveStream)
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):

    list_display = (
        'user',
        'avatar'
    )
@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'sender',
        'guest_name',
        'room',
        'message_preview',
        'created_at'
    )

    list_filter = (
        'room',
        'created_at',
    )

    search_fields = (
        'message',
        'room',
        'sender__username',
        'guest_name',
    )

    readonly_fields = (
        'created_at',
    )


    def message_preview(self, obj):

        if obj.message:
            return obj.message[:50]

        if obj.file:
            return obj.file.name[:50]

        return "Empty"

    message_preview.short_description = "Message"
 

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "title",
        "is_read",
        "created_at"
    )

    list_filter = (
        "is_read",
        "created_at"
    )   
    
from .models import Movie


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):

    list_display = (
        "title",
        "year",
        "duration"
    )


