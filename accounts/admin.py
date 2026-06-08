from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from .models import Contact
admin.site.site_header = "JOHBOY SETUPS ADMIN"
admin.site.site_title = "JOHBOY SETUPS"
admin.site.index_title = "Welcome to JOHBOY SETUPS Dashboard"
admin.site.register(Contact)

admin.site.unregister(User)
admin.site.register(User, UserAdmin)