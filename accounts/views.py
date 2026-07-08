import json
import random
import requests
from django.views.decorators.clickjacking import xframe_options_exempt
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
    PasswordResetOTP, Profile, ChatMessage, ChatMemory
)

from .forms import RegisterForm, ContactForm
from .email_service import send_otp_email
from django.contrib.auth.models import User


# =========================
# 🧠 GEMINI AI FUNCTIONS
# =========================
def get_memory(user, limit=10):
    if not user or not user.is_authenticated:
        return ""

    msgs = ChatMemory.objects.filter(user=user).order_by("-created_at")[:5]
    msgs = reversed(msgs)

    memory_text = ""
    for m in msgs:
        memory_text += f"{m.role.upper()}: {m.message}\n"

    return memory_text
def build_context(message):

    tutorials = Tutorial.objects.filter(
        Q(title__icontains=message) |
        Q(description__icontains=message)
    )[:5]

    software = Software.objects.filter(
        Q(name__icontains=message) |
        Q(description__icontains=message)
    )[:5]

    categories = Category.objects.all()[:10]

    context = "\n=== WEBSITE INFORMATION ===\n"

    context += "\n📌 PAGES AVAILABLE:\n"
    context += "- Home page /\n"
    context += "- Tutorials /tutorials/\n"
    context += "- Software /software/\n"
    context += "- Livestreams /livestreams/\n"
    context += "- Contact /contactus/\n"
    context += "- About /about/\n"

    context += "\n📂 CATEGORIES:\n"
    for c in categories:
        context += f"- {c.name}: /category/{c.id}/\n"

    context += "\n📚 TUTORIALS:\n"
    for t in tutorials:
        context += f"- {t.title} → /tutorial/{t.id}/\n"

    context += "\n💾 SOFTWARE:\n"
    for s in software:
        context += f"- {s.name} → /software/{s.id}/\n"

    return context
def gemini_ai(message, context="", memory=""):
    api_key = settings.GEMINI_API_KEY

    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={api_key}"

    prompt = f"""
SYSTEM INSTRUCTIONS:
You are JMJ Softwares AI Assistant.

COMMAND RULES:
- If user asks "what is this website" → explain full website clearly
- If user asks "where is tutorials" → give /tutorials/
- If user asks "software/downloads" → guide to /software/
- If user asks "contact" → give /contactus/
-if user asks  "about" → give /about/
-if user asks  'how to use this website' → explain clearly
-if user aks   'how to register ' explain the instuction on register
- Always respond in Swahili or English depending on user
- Be short, clear, helpful
- NEVER invent fake pages
-if user want to solve some math issue solve it
-show empathy and be friendly
-provide the good advaice
-show reference
-provide the good advices and solutions to the user
-provide image,diagram if needed


WEBSITE KNOWLEDGE:
{context}

CHAT MEMORY:
{memory}

USER MESSAGE:
{message}
"""

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }

    try:
        r = requests.post(url, json=payload, timeout=15)

        # DEBUG
        print("GEMINI STATUS:", r.status_code)
        print("GEMINI RAW:", r.text)

        data = r.json()

        if "candidates" not in data:
            return f"Gemini error: {data}"

        return data["candidates"][0]["content"]["parts"][0]["text"]

    except Exception as e:
        return f"Gemini request failed: {str(e)}"


# =========================
# 🚀 AI ASSISTANT API
# =========================
def ai_assistant_api(request):

    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=400)

    try:
        data = json.loads(request.body.decode("utf-8"))
    except:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    message = data.get("message", "").strip()

    if not message:
        return JsonResponse({"error": "empty message"}, status=400)

    context = build_context(message)
    memory = get_memory(request.user)

    # SAVE USER MESSAGE
    if request.user.is_authenticated:
        ChatMemory.objects.create(
            user=request.user,
            role="user",
            message=message
        )

    # GET AI RESPONSE
    answer = gemini_ai(message, context, memory)

    # SAVE AI RESPONSE
    if request.user.is_authenticated:
        ChatMemory.objects.create(
            user=request.user,
            role="ai",
            message=answer
        )

    return JsonResponse({"answer": answer})
@csrf_exempt
def ai_assistant(request):
    return render(request, "ai_assistant.html")
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
def webb_page(request):
    return render(request, 'webb.html')
def os_page(request):
    return render(request, 'os.html')
def security_page(request):
    return render(request, 'security.html')
def utilities(request):
    softwares = Software.objects.filter(category__name__iexact="Utilities")
    return render(request, 'utilities.html', {'softwares': softwares})
def design(request):
    softwares = Software.objects.filter(category__name__iexact="Design")
    return render(request, 'design.html', {'softwares': softwares})
def development(request):
    softwares = Software.objects.filter(category__name__iexact="Development")
    return render(request, 'development.html', {'softwares': softwares})
def simulation_page(request):
    softwares = Software.objects.filter(category__name__iexact="Simulation")
    return render(request, 'simulation.html', {'softwares': softwares})
def category_softwares(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    softwares = Software.objects.filter(category=category)
    return render(request, 'category_softwares.html', {
        'category': category,
        'softwares': softwares
    })





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

@login_required
def chat_home(request):

    users = User.objects.exclude(id=request.user.id)

    selected_user = None

    messages = []

    username = request.GET.get("user")

    if username:

        try:

            selected_user = User.objects.get(username=username)

            room = "_".join(
                sorted([
                    request.user.username,
                    selected_user.username
                ])
            )

            messages = ChatMessage.objects.filter(
                room=room
            ).order_by("created_at")

        except User.DoesNotExist:

            pass

    return render(request,"chat/chat.html",{

        "users":users,

        "selected_user":selected_user,

        "messages":messages

    })