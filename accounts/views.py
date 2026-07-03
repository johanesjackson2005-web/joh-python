from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
import random

from .models import Category

from .forms import RegisterForm, ContactForm
from .models import PasswordResetOTP
from .email_service import send_otp_email
from django.shortcuts import render, get_object_or_404
from .models import Category, Software
def home(request):
    categories = Category.objects.all()

    return render(request, "home.html", {
        "categories": categories
    })

from django.contrib import messages
from django.contrib.auth.models import User

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)

        if form.is_valid():

            email = form.cleaned_data['email']

            # CHECK IF EMAIL EXISTS
            if User.objects.filter(email=email).exists():
                messages.error(request, "Email already exists")
                return redirect('register')

            # CREATE USER
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()

            messages.success(request, "Account created successfully")
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
        messages.error(request, 'Invalid username or password')
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

def contactus(request):

    if request.method == 'POST':

        form = ContactForm(request.POST)

        if form.is_valid():

            form.save()

            messages.success(
                request,
                'Thank you! We received your message.'
            )

    else:
        form = ContactForm()

    return render(
        request,
        'contact.html',
        {'form': form}
    )
def slideshow(request):
    return render(request, 'slideshow.html')
def about(request):
    return render(request, 'about.html')

def forgot_password(request):

    if request.method == "POST":

        email = request.POST.get("email")

        user = User.objects.filter(email=email).first()

        if not user:
            messages.error(request, "Email does not exist")
            return redirect("forgot_password")

        otp = str(random.randint(100000, 999999))

        try:

            PasswordResetOTP.objects.create(
                user=user,
                otp=otp
            )

            success = send_otp_email(email, otp)

            if not success:
                messages.error(request, "Failed to send OTP")
                return redirect("forgot_password")

            request.session["reset_email"] = email

            messages.success(request, "OTP sent successfully")

            return redirect("verify_otp")

        except Exception as e:

            print("RESET ERROR:", str(e))

            messages.error(
                request,
                "System error occurred"
            )

            return redirect("forgot_password")

    return render(request, "forgot_password.html")
def verify_otp(request):

    if request.method == "POST":

        entered_otp = request.POST.get("otp")

        email = request.session.get("reset_email")

        user = User.objects.filter(email=email).first()

        if not user:
            messages.error(request, "Session expired")
            return redirect("forgot_password")

        otp_obj = PasswordResetOTP.objects.filter(
            user=user,
            otp=entered_otp
        ).last()

        if not otp_obj:
            messages.error(request, "Invalid OTP")
            return redirect("verify_otp")

        request.session["otp_verified"] = True

        messages.success(
            request,
            "OTP verified successfully"
        )

        return redirect("reset_password")

    return render(request, "verify_otp.html")
def reset_password(request):

    if not request.session.get("otp_verified"):
        messages.error(request, "OTP verification required")
        return redirect("forgot_password")

    if request.method == "POST":

        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        if password1 != password2:
            messages.error(request, "Passwords do not match")
            return redirect("reset_password")

        email = request.session.get("reset_email")

        user = User.objects.filter(email=email).first()

        if not user:
            messages.error(request, "User not found")
            return redirect("forgot_password")

        user.set_password(password1)
        user.save()

        request.session.flush()

        messages.success(
            request,
            "Password changed successfully"
        )

        return redirect("login")

    return render(request, "reset_password.html")

def webb_page(request):
    return render(request, 'webb.html')


def os_page(request):
    return render(request, 'os.html')


def security_page(request):
    return render(request, 'security.html')


def simulation_page(request):
    return render(request, 'simulation.html') 

def utilities(request):
    return render(request, 'utilities.html')


def design(request):
    return render(request, 'design.html')


def development(request):
    return render(request, 'development.html')

def category_softwares(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    softwares = Software.objects.filter(category=category)

    return render(request, "software.html", {
        "category": category,
        "softwares": softwares
    })