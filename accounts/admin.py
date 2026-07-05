from django.contrib import admin
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
@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'room', 'created_at')
    search_fields = ('room', 'message')
    readonly_fields = ('created_at',)