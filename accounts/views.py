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
from django.core.files.storage import default_storage
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from .models import (
    Software, Tutorial, Category, LiveStream,
    PasswordResetOTP, Profile, ChatMessage, ChatMemory
)
from .models import Notification

import os
import mimetypes
import base64
import requests
from django.conf import settings

from .forms import RegisterForm, ContactForm
from .email_service import send_otp_email
from django.contrib.auth.models import User
import os
import mimetypes
from .prompts import JMJ_SYSTEM_PROMPT
# =========================
# 🧠 GEMINI AI FUNCTIONS
# =========================
def get_memory(user, limit=10):

    if not user or not user.is_authenticated:
        return ""

    messages = ChatMemory.objects.filter(
        user=user
    ).order_by(
        "-created_at"
    )[:limit]


    messages = reversed(messages)


    memory_text = ""

    for msg in messages:

        memory_text += (
            f"{msg.role.upper()}: "
            f"{msg.message}\n"
        )


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



def gemini_ai(message, context="", memory="", file_path=None, user=None):

    api_key = settings.GEMINI_API_KEY
    user_info = "User name: Guest"

    if user and user.is_authenticated:

      name = user.first_name or user.username

      user_info = f"""
     USER INFORMATION:

     Name:
    {name}

You may address the user by this name naturally.
"""
    url = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"gemini-2.5-flash:generateContent?key={api_key}"
)

    user_prompt = f"""

    {user_info}


 WEBSITE KNOWLEDGE:

 {context}


 CHAT MEMORY:

 {memory}


 USER MESSAGE:

 {message}

"""
    # Text part
    parts = [
    {
        "text": user_prompt
    }
]

    # Optional image
    if file_path:

        full_path = os.path.join(
            settings.MEDIA_ROOT,
            file_path
        )

        if os.path.exists(full_path):

            mime_type = mimetypes.guess_type(full_path)[0]

            if mime_type and mime_type.startswith("image"):

                with open(full_path, "rb") as f:

                    image_data = base64.b64encode(
                        f.read()
                    ).decode()

                parts.append(
                    {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": image_data
                        }
                    }
                )

    payload = {

     "systemInstruction"  : {

        "parts": [
            {
                "text": JMJ_SYSTEM_PROMPT
            }
        ]

    },

    "contents": [

        {
            "parts": parts
        }

    ]

}

    try:

        r = requests.post(
    url,
    headers={
        "Content-Type": "application/json"
    },
    json=payload,
    timeout=30
)
        print("STATUS:", r.status_code)
        print("RAW:", r.text)

        data = r.json()

        if "candidates" not in data:
            return str(data)

        return data["candidates"][0]["content"]["parts"][0]["text"]

    except Exception as e:
        return str(e)
# =========================
# 🚀 AI ASSISTANT API
# =========================
@csrf_exempt
def ai_assistant_api(request):

    if request.method != "POST":
        return JsonResponse(
            {"error": "POST required"},
            status=400
        )

    uploaded_file = None

    # multipart/form-data (text + file)
    if request.content_type and request.content_type.startswith("multipart"):

        message = request.POST.get(
            "message",
            ""
        ).strip()

        uploaded_file = request.FILES.get("file")

    # application/json (text only)
    else:

        try:
            data = json.loads(
                request.body.decode("utf-8")
            )

        except Exception:

            return JsonResponse(
                {"error":"Invalid JSON"},
                status=400
            )

        message = data.get(
            "message",
            ""
        ).strip()

    if not message and not uploaded_file:

        return JsonResponse(
            {
                "error":"Message or file required"
            },
            status=400
        )

    file_path = None

    if uploaded_file:

        MAX_SIZE = 3* 1024 * 1024

        if uploaded_file.size > MAX_SIZE:

            return JsonResponse(
                {
                    "error":"Maximum file size is 5 MB"
                },
                status=400
            )

        file_path = default_storage.save(

            "ai_uploads/" + uploaded_file.name,

            uploaded_file

        )

    context = build_context(message)

    memory = get_memory(request.user)

    if request.user.is_authenticated:

        ChatMemory.objects.create(

            user=request.user,

            role="user",

            message=message if message else "[Uploaded File]"

        )

    answer = gemini_ai(

        message,

        context,

        memory,

        file_path,
        request.user

    )

    if request.user.is_authenticated:

        ChatMemory.objects.create(

            user=request.user,

            role="ai",

            message=answer

        )

    return JsonResponse({

        "answer":answer,

        "file":file_path

    })
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

from django.contrib.auth.models import User

def home(request):

    categories = Category.objects.all()
    tutorials = Tutorial.objects.order_by("-created_at")[:6]
    livestreams = LiveStream.objects.order_by("-created_at")[:4]

    users = User.objects.filter(is_active=True)

    if request.user.is_authenticated:

        profile, _ = Profile.objects.get_or_create(user=request.user)

        if profile.avatar == "default.jpg":
            return redirect("choose_avatar")

        # usijionyeshe mwenyewe kwenye list
        users = users.exclude(id=request.user.id)

    else:

        users = User.objects.none()

    return render(request, "home.html", {

        "categories": categories,
        "tutorials": tutorials,
        "livestreams": livestreams,
        "users": users,

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




@login_required
def notifications(request):

    notifications = Notification.objects.filter(
        user=request.user
    ).order_by(
        "-created_at"
    )


    return render(
        request,
        "notifications.html",
        {
            "notifications": notifications
        }
    )


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
def users_search(request):

    query = request.GET.get('q', '')

    users = User.objects.filter(
        username__icontains=query
    )[:10]

    data = []

    for user in users:
        data.append({
            "id": user.id,
            "username": user.username
        })

    return JsonResponse(data, safe=False)

@login_required
def chat_home(request):

    users = User.objects.exclude(id=request.user.id)

    room_name = request.GET.get("room", "public")

    selected_user = None

    # PRIVATE ROOM
    if room_name.startswith("pm_"):

        parts = room_name.replace("pm_", "").split("_")

        for username in parts:

            if username.lower() != request.user.username.lower():

                try:
                    selected_user = User.objects.get(
                        username__iexact=username
                    )
                except User.DoesNotExist:
                    pass

                break

    # Kama umeingia kupitia ?user=flora
    username = request.GET.get("user")



    if username:

        try:

           selected_user = User.objects.get(
            username__iexact=username
        )


           names = sorted([
            request.user.username.lower(),
            selected_user.username.lower()
        ])


           room_name = f"pm_{names[0]}_{names[1]}"


        except User.DoesNotExist:

           selected_user = None
           
    messages = ChatMessage.objects.filter(
        room=room_name
    ).order_by("created_at")
    
    request.session['previous_page'] = request.META.get(
    'HTTP_REFERER',
    '/')
    return render(request, "chat.html", {
        "users": users,
        "selected_user": selected_user,
        "messages": messages,
        "room_name": room_name,
        "is_public": room_name == "public",
    })
@csrf_exempt
def chat_upload(request):

    print("UPLOAD VIEW CALLED")

    if request.method != "POST":
        return JsonResponse({
            "error": "POST required"
        }, status=400)


    try:
        
         uploaded_file = request.FILES.get("file")
         if not uploaded_file:

            return JsonResponse({
                "error": "No file selected"
            }, status=400)


        
        
         MAX_SIZE = 5 * 1024 * 1024   # 2 MB

         if uploaded_file.size > MAX_SIZE:
           return JsonResponse(
        {
            "error": "Maximum file size is 5 MB."
        },
        status=400
       )
         print("FILE:", uploaded_file)


       

        # save file kwenye MEDIA
         file_path = default_storage.save(
            f"chat/uploads/{uploaded_file.name}",
            uploaded_file
        )


         file_url = default_storage.url(file_path)


         print("SAVED:", file_path)
         print("URL:", file_url)


        # ===============================
        # SAVE FILE AS CHAT MESSAGE
        # ===============================

         user = request.user if request.user.is_authenticated else None

         room = request.POST.get(
            "room",
            "public"
        )


         chat_message = ChatMessage.objects.create(

            sender=user,

            guest_name=None if user else "Guest",

            room=room,

            message="",

            file=file_path

        )


         print(
            "CHAT MESSAGE SAVED:",
            chat_message.id
        )


         return JsonResponse({

            "id": chat_message.id,

            "url": file_url,

            "name": uploaded_file.name

        })


    except Exception as e:

        print("UPLOAD ERROR:", str(e))

        return JsonResponse({

            "error": str(e)

        }, status=500)
@csrf_exempt
def ai_upload(request):

    if request.method != "POST":
        return JsonResponse({"error":"POST required"}, status=400)

    uploaded_file = request.FILES.get("file")

    if not uploaded_file:
        return JsonResponse({"error":"No file"}, status=400)

    MAX_SIZE = 5 * 1024 * 1024

    if uploaded_file.size > MAX_SIZE:
        return JsonResponse(
            {"error":"Maximum file size is 5 MB"},
            status=400
        )

    path = default_storage.save(
        f"ai_uploads/{uploaded_file.name}",
        uploaded_file
    )

    return JsonResponse({

        "url": default_storage.url(path),

        "path": path,

        "name": uploaded_file.name,

        "type": uploaded_file.content_type

    })


def add_tutorial(request):

    # mfano tutorial imeongezwa
    tutorial = Tutorial.objects.create(
        title="Django Authentication"
    )


    users = User.objects.all()


    for user in users:

        Notification.objects.create(

            user=user,

            title="New Tutorial Available",

            message=f"Tutorial mpya imeongezwa: {tutorial.title}"

        )