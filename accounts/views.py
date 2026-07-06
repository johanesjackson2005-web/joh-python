import json
import random
import requests

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.views.decorators.clickjacking import xframe_options_exempt
from django.conf import settings
from django.db.models import Q

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from .models import (
    Software, Tutorial, Category, LiveStream,
    PasswordResetOTP, Profile, ChatMessage
)

from .forms import RegisterForm, ContactForm
from .email_service import send_otp_email


# =========================
# 🧠 GEMINI AI FUNCTIONS
# =========================

def build_context(message):

    tutorials = Tutorial.objects.filter(
        Q(title__icontains=message) |
        Q(description__icontains=message)
    )[:5]

    software = Software.objects.filter(
        Q(name__icontains=message) |
        Q(description__icontains=message)
    )[:5]

    context = ""

    if tutorials.exists():
        context += "TUTORIALS:\n"
        for t in tutorials:
            context += f"- {t.title} (/tutorials/{t.id})\n"

    if software.exists():
        context += "\nSOFTWARE:\n"
        for s in software:
            context += f"- {s.name} (/software/{s.id})\n"

    return context


def gemini_ai(message, context=""):

    api_key = settings.GEMINI_API_KEY

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"

    prompt = f"""
You are a smart AI assistant for JMJ Softwares website.

Rules:
- Be helpful and short
- Use Swahili or English
- Guide users to correct pages
- Use context if available

Website context:
{context}

User question:
{message}
"""

    payload = {
        "contents": [
            {"parts": [{"text": prompt}]}
        ]
    }

    try:
        r = requests.post(url, json=payload, timeout=15)
        return r.json()['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        return "AI error: " + str(e)


# =========================
# 🚀 AI ASSISTANT API
# =========================

def ai_assistant_api(request):

    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=400)

    try:
        data = json.loads(request.body.decode("utf-8"))
        message = data.get("message", "").strip()
    except:
        return JsonResponse({"error": "invalid request"}, status=400)

    if not message:
        return JsonResponse({"error": "empty message"}, status=400)

    context = build_context(message)
    answer = gemini_ai(message, context)

    return JsonResponse({"answer": answer})


# =========================
# 💬 CHAT (WebSocket fallback)
# =========================

@csrf_exempt
def chat_send(request):

    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except:
        data = request.POST.dict()

    message = data.get('message')
    room = data.get('room', 'public')

    if not message:
        return JsonResponse({'error': 'message required'}, status=400)

    user = request.user if request.user.is_authenticated else None
    username = user.username if user else data.get('username', 'Anonymous')

    try:
        ChatMessage.objects.create(sender=user, room=room, message=message)
    except:
        pass

    try:
        channel_layer = get_channel_layer()
        payload = {'message': message, 'user': username}

        async_to_sync(channel_layer.group_send)(
            f'chat_{room}',
            {
                'type': 'chat.message',
                'text': json.dumps(payload)
            }
        )
    except:
        pass

    return JsonResponse({'message': message, 'user': username})


@staff_member_required
def admin_chat(request):
    users = get_user_model().objects.all().order_by('username')
    return render(request, 'admin_chat.html', {'users': users})


# =========================
# 🏠 MAIN PAGES
# =========================

def home(request):

    categories = Category.objects.all()
    tutorials = Tutorial.objects.order_by("-created_at")[:6]
    livestreams = LiveStream.objects.order_by("-created_at")[:4]

    if request.user.is_authenticated:
        profile, _ = Profile.objects.get_or_create(user=request.user)

        if profile.avatar == "default.jpg":
            return redirect("choose_avatar")

    return render(request, "home.html", {
        "categories": categories,
        "tutorials": tutorials,
        "livestreams": livestreams
    })


def about(request):
    return render(request, 'about.html')


def slideshow(request):
    return render(request, 'slideshow.html')
def web_page(request):
    return render(request, 'webb.html')


# =========================
# 🔐 AUTH
# =========================

def register(request):

    if request.method == 'POST':
        form = RegisterForm(request.POST)

        if form.is_valid():

            email = form.cleaned_data['email']

            if get_user_model().objects.filter(email=email).exists():
                messages.error(request, "Email already exists")
                return redirect('register')

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

        messages.error(request, 'Invalid credentials')

    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


# =========================
# 📩 CONTACT
# =========================

def contactus(request):

    if request.method == 'POST':
        form = ContactForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, "Message sent successfully")
            return redirect('contactus')

    else:
        form = ContactForm()

    return render(request, 'contact.html', {'form': form})


# =========================
# 🔑 PASSWORD RESET
# =========================

def forgot_password(request):

    if request.method == "POST":

        email = request.POST.get("email")
        user = get_user_model().objects.filter(email=email).first()

        if not user:
            messages.error(request, "Email not found")
            return redirect("forgot_password")

        otp = str(random.randint(100000, 999999))

        PasswordResetOTP.objects.create(user=user, otp=otp)
        send_otp_email(email, otp)

        request.session["reset_email"] = email

        messages.success(request, "OTP sent")
        return redirect("verify_otp")

    return render(request, "forgot_password.html")


def verify_otp(request):

    if request.method == "POST":

        otp = request.POST.get("otp")
        email = request.session.get("reset_email")

        user = get_user_model().objects.filter(email=email).first()

        otp_obj = PasswordResetOTP.objects.filter(user=user, otp=otp).last()

        if otp_obj:
            request.session["otp_verified"] = True
            return redirect("reset_password")

        messages.error(request, "Invalid OTP")

    return render(request, "verify_otp.html")


def reset_password(request):

    if not request.session.get("otp_verified"):
        return redirect("forgot_password")

    if request.method == "POST":

        p1 = request.POST.get("password1")
        p2 = request.POST.get("password2")

        if p1 != p2:
            messages.error(request, "Passwords do not match")
            return redirect("reset_password")

        email = request.session.get("reset_email")
        user = get_user_model().objects.filter(email=email).first()

        user.set_password(p1)
        user.save()

        request.session.flush()

        return redirect("login")

    return render(request, "reset_password.html")


# =========================
# 📚 CONTENT PAGES
# =========================

def tutorials(request):
    tutorials = Tutorial.objects.all().order_by("-created_at")
    return render(request, "tutorials.html", {"tutorials": tutorials})


def tutorial_detail(request, tutorial_id):

    tutorial = get_object_or_404(Tutorial, id=tutorial_id)

    related = Tutorial.objects.filter(
        category=tutorial.category
    ).exclude(id=tutorial.id)[:4]

    return render(request, "tutorial_detail.html", {
        "tutorial": tutorial,
        "related": related
    })


def livestreams(request):
    livestreams = LiveStream.objects.order_by("-created_at")
    return render(request, "livestreams.html", {"livestreams": livestreams})


def search_view(request):

    query = request.GET.get("q", "")

    tutorial_results = Tutorial.objects.filter(title__icontains=query)
    software_results = Software.objects.filter(name__icontains=query)
    category_results = Category.objects.filter(name__icontains=query)
    livestream_results = LiveStream.objects.filter(title__icontains=query)

    return render(request, "search.html", {
        "query": query,
        "tutorial_results": tutorial_results,
        "software_results": software_results,
        "category_results": category_results,
        "livestream_results": livestream_results
    })


# =========================
# 🎭 PROFILE
# =========================

@login_required
def choose_avatar(request):

    profile = request.user.profile
    avatars = [f"avatar{i}.jpg" for i in range(1, 71)]

    if request.method == "POST":
        profile.avatar = request.POST.get("avatar")
        profile.save()
        return redirect("home")

    return render(request, "choose_avatar.html", {"avatars": avatars})