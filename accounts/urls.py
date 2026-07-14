from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('contactus/',views.contactus, name='contactus'),
    path('slideshow/', views.slideshow, name='slideshow'),
    path('about/', views.about, name='about'),
    path(
        'forgot-password/',
        views.forgot_password,
        name='forgot_password'
    ),

    path(
        'verify-otp/',
        views.verify_otp,
        name='verify_otp'
    ),

    path(
        'reset-password/',
        views.reset_password,
        name='reset_password'
    ),
    path('webb/', views.webb_page, name='webb'),
    path('os/', views.os_page, name='os'),
    path('security/', views.security_page, name='security'),
    path('utilities/', views.utilities, name='utilities'),
    path('design/', views.design, name='design'),
    path('development/', views.development, name='development'),
    path('simulation/', views.simulation_page, name='simulation'),
     path("category/<int:category_id>/", views.category_softwares, name="category_softwares"),
     path("tutorials/", views.tutorials, name="tutorials"),
     path("livestreams/", views.livestreams, name="livestreams"),
    path(
    "tutorial/<int:tutorial_id>/",
    views.tutorial_detail,
    name="tutorial_detail"
),
    path("search/", views.search_view, name="search"),
    path("choose-avatar/", views.choose_avatar, name="choose_avatar"),
    path("ai-assistant/", views.ai_assistant),        # HTML
    path("ai-assistant/api/", views.ai_assistant_api),
    path('admin-chat/', views.admin_chat, name='admin_chat'),
    path('chat/send/', views.chat_send, name='chat_send'),
     path("chat/", views.chat_home, name="chat_home"),
     path(
    "accounts/users/search/",
    views.users_search,
    name="users_search"
),
     path("chat/upload/", views.chat_upload, name="chat_upload"),
    path("ai/upload/", views.ai_upload, name="ai_upload"),
    path(
    'users-search/',
    views.users_search,
    name='users_search'
),
    path(
    "notifications/",
    views.notifications,
    name="notifications"
),
path(
    "movies/",
    views.movies,
    name="movies"
),
]