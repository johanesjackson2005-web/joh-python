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
]
