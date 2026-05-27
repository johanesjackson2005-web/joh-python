from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required
import random
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.contrib import messages
from django.conf import settings
from .forms import RegisterForm , ContactForm
from .models import PasswordResetOTP


def home(request):
    return render(request, 'home.html')

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            return redirect('login')
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            return redirect('home')
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('login')


def contactus(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            message = form.cleaned_data['message']
            
            # Send email (optional - configure email backend in settings)
            try:
                send_mail(
                    f'Contact from {username}',
                    message,
                    email,
                    [settings.DEFAULT_FROM_EMAIL or 'johboy2026@gmail.com'],
                    fail_silently=True
                )
            except:
                pass
            
            return render(request, 'contact.html', {'success': 'Thank you! We will contact you soon.'})
        else:
            form=ContactForm()
    return render(request, 'contact.html')
def slideshow(request):
    return render(request, 'slideshow.html')
def about(request):
    return render(request, 'about.html')



def forgot_password(request):

    if request.method == 'POST':

        email = request.POST.get('email')

        try:
            user = User.objects.get(email=email)

            otp = str(random.randint(100000, 999999))

            PasswordResetOTP.objects.create(
                user=user,
                otp=otp
            )

            send_mail(
                'Password Reset OTP',
                f'Your OTP is: {otp}',
                'johanesjackson2005@gmail.com',
                [email],
                fail_silently=False,
            )

            request.session['reset_email'] = email

            return redirect('verify_otp')

        except User.DoesNotExist:
            messages.error(request, 'Email does not exist')

    return render(request, 'forgot_password.html')


def verify_otp(request):

    if request.method == 'POST':

        entered_otp = request.POST.get('otp')

        email = request.session.get('reset_email')

        user = User.objects.get(email=email)

        otp_obj = PasswordResetOTP.objects.filter(
            user=user,
            otp=entered_otp
        ).last()

        if otp_obj:
            request.session['otp_verified'] = True
            return redirect('reset_password')

        else:
            messages.error(request, 'Invalid OTP')

    return render(request, 'verify_otp.html')


def reset_password(request):

    if not request.session.get('otp_verified'):
        messages.error(request, 'OTP verification required')
        return redirect('forgot_password')

    if request.method == 'POST':

        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if password1 == password2:

            email = request.session.get('reset_email')

            user = User.objects.get(email=email)

            user.set_password(password1)
            user.save()

            messages.success(request, 'Password changed successfully')

            return redirect('login')

        else:
            messages.error(request, 'Passwords do not match')

    return render(request, 'reset_password.html')
    
    

# Create your views here.
