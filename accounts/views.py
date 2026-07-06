from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
import random
from django.db.models import Q
from .models import Software, Tutorial, Category, LiveStream
from .forms import RegisterForm, ContactForm
from .models import PasswordResetOTP, Profile
from .email_service import send_otp_email
from django.shortcuts import render, get_object_or_404
from .models import Category, Software, Tutorial
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .models import Category, Tutorial, LiveStream, Profile
from django.http import JsonResponse
from django.conf import settings
import json
import requests
from django.contrib.admin.views.decorators import staff_member_required

from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.views.decorators.clickjacking import xframe_options_exempt
from django.http import HttpResponse
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.http import JsonResponse
from django.contrib.auth import get_user_model


@csrf_exempt
def chat_send(request):
    """Fallback HTTP endpoint to persist chat messages when WebSocket is unavailable.

    Accepts POST with JSON: {message, room} or form-encoded data. Returns JSON with
    {'message': ..., 'user': username} on success.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body.decode('utf-8') or '{}')
        else:
            data = request.POST.dict()
    except Exception:
        data = {}

    message = data.get('message')
    room = data.get('room', 'public')

    if not message:
        return JsonResponse({'error': 'message required'}, status=400)

    user = request.user if getattr(request, 'user', None) and request.user.is_authenticated else None
    username = user.username if user else data.get('username', 'Anonymous')

    try:
        ChatMessage.objects.create(sender=user, room=room, message=message)
    except Exception:
        # ignore persistence errors but continue
        pass

    # Broadcast to the channel layer so connected WebSocket clients in the room see the message
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
    except Exception:
        # do not fail the request if broadcasting fails
        pass

    return JsonResponse({'message': message, 'user': username})

@staff_member_required
def admin_chat(request):
    """Admin chat UI to open a per-user room and message the user in real-time."""
    users = User.objects.all().order_by('username')
    return render(request, 'admin_chat.html', {'users': users})

def home(request):

    categories = Category.objects.all()
    tutorials = Tutorial.objects.order_by("-created_at")[:6]
    livestreams = LiveStream.objects.order_by("-created_at")[:4]

    if request.user.is_authenticated:

        profile, _ = Profile.objects.get_or_create(user=request.user)

        # CRITICAL CONTROL LOGIC
        if profile.avatar == "default.jpg":
            return redirect("choose_avatar")

    return render(request, "home.html", {
        "categories": categories,
        "tutorials": tutorials,
        "livestreams": livestreams
    })

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)

        if form.is_valid():

            email = form.cleaned_data['email']

            if User.objects.filter(email=email).exists():
                messages.error(request, "⚠️Email already exists")
                return redirect('register')

            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()

            # Save selected avatar here

            messages.success(request, "✅Account created successfully")
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
        messages.error(request, '⚠️ Invalid username or password')
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
            messages.error(request, "⚠️Email does not exist")
            return redirect("forgot_password")

        otp = str(random.randint(100000, 999999))

        try:

            PasswordResetOTP.objects.create(
                user=user,
                otp=otp
            )

            success = send_otp_email(email, otp)

            if not success:
                messages.error(request, "⚠️Failed to send OTP")
                return redirect("forgot_password")

            request.session["reset_email"] = email

            messages.success(request, "✅OTP sent successfully   check your email inbox or spam folder for the OTP")

            return redirect("verify_otp")

        except Exception as e:

            print("RESET ERROR:", str(e))

            messages.error(
                request,
                "⚠️ System error occurred"
            )

            return redirect("forgot_password")

    return render(request, "forgot_password.html")
def verify_otp(request):

    if request.method == "POST":

        entered_otp = request.POST.get("otp")

        email = request.session.get("reset_email")

        user = User.objects.filter(email=email).first()

        if not user:
            messages.error(request, "⚠️Session expired")
            return redirect("forgot_password")

        otp_obj = PasswordResetOTP.objects.filter(
            user=user,
            otp=entered_otp
        ).last()

        if not otp_obj:
            messages.error(request, "⚠️Invalid OTP")
            return redirect("verify_otp")

        request.session["otp_verified"] = True

        messages.success(
            request,
            "✅OTP verified successfully  You can now reset your password."
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
            messages.error(request, "⚠️ User not found")
            return redirect("forgot_password")

        user.set_password(password1)
        user.save()

        request.session.flush()

        messages.success(
            request,
            "✅Password changed successfully now you can login with your new password"
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

def tutorials(request):
    tutorials = Tutorial.objects.all().order_by("-created_at")

    return render(request, "tutorials.html", {
        "tutorials": tutorials
    })
def tutorial_detail(request, tutorial_id):
    tutorial = get_object_or_404(Tutorial, id=tutorial_id)

    related = Tutorial.objects.filter(
        category=tutorial.category
    ).exclude(id=tutorial.id)[:4]

    return render(request, "tutorial_detail.html", {
        "tutorial": tutorial,
        "related": related,
    })
def livestreams(request):

    livestreams = LiveStream.objects.order_by("-created_at")

    return render(
        request,
        "livestreams.html",
        {
            "livestreams": livestreams
        }
    )
def search_view(request):
    query = request.GET.get("q", "")

    tutorial_results = Tutorial.objects.filter(
        Q(title__icontains=query) |
        Q(description__icontains=query) |
        Q(instructor__icontains=query) |
        Q(category__name__icontains=query)
    )

    software_results = Software.objects.filter(
        Q(name__icontains=query) |
        Q(description__icontains=query) |
        Q(category__name__icontains=query)
    )

    category_results = Category.objects.filter(
        Q(name__icontains=query) |
        Q(description__icontains=query)
    )

    livestream_results = LiveStream.objects.filter(
        Q(title__icontains=query) |
        Q(description__icontains=query)
    )

    return render(request, "search.html", {
        "query": query,
        "tutorial_results": tutorial_results,
        "software_results": software_results,
        "category_results": category_results,
        "livestream_results": livestream_results,
    })


@login_required
def choose_avatar(request):

    profile = request.user.profile
    avatars = [f"avatar{i}.jpg" for i in range(1, 71)]

    if request.method == "POST":
        selected = request.POST.get("avatar")

        profile.avatar = selected
        profile.save()

        return redirect("home")

    return render(request, "choose_avatar.html", {
        "avatars": avatars
    })


@xframe_options_exempt
@ensure_csrf_cookie
def ai_assistant(request):
    """Render AI assistant chat page.

    Exempt from X-Frame-Options so the page can be embedded in a site-wide iframe/widget.
    """
    return render(request, 'ai_assistant.html')


def healthz(request):
    """Simple health endpoint to verify the app is responding."""
    return JsonResponse({'status': 'ok'})


def header_inspector(request):
    """Return key response headers as seen after clickjacking middleware.

    This manually runs the XFrameOptions middleware to show whether
    the `X-Frame-Options` header would be present for a normal response.
    Use this to confirm embedding is allowed on the deployed host.
    """
    from django.middleware.clickjacking import XFrameOptionsMiddleware

    resp = JsonResponse({'ok': True})
    try:
        # Let the middleware attach any frame options header it would normally add
        processed = XFrameOptionsMiddleware().process_response(request, resp)
        if processed is not None:
            resp = processed
    except Exception:
        pass

    keys = ['X-Frame-Options', 'Content-Security-Policy']
    headers = {k: resp.get(k) for k in keys}
    return JsonResponse({'headers': headers})

def ai_assistant_api(request):
    """Smart AI Assistant API"""

    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=400)

    try:
        payload = json.loads(request.body.decode('utf-8'))
        message = payload.get('message', '').strip()
    except:
        return JsonResponse({'error': 'invalid request'}, status=400)

    if not message:
        return JsonResponse({'error': 'empty message'}, status=400)

    api_key = getattr(settings, 'OPENAI_API_KEY', None)

    # 🔴 If no API key → fallback
    if not api_key:
        return JsonResponse({
            'answer': "AI is not configured. Please set OPENAI_API_KEY."
        })

    # 🧠 OPTIONAL: your site knowledge (RAG)
    try:
        tutorial_hits = Tutorial.objects.filter(
            Q(title__icontains=message) | Q(description__icontains=message)
        )[:3]

        software_hits = Software.objects.filter(
            Q(name__icontains=message) | Q(description__icontains=message)
        )[:3]

        context = ""

        if tutorial_hits:
            context += "Tutorials:\n"
            for t in tutorial_hits:
                context += f"- {t.title}\n"

        if software_hits:
            context += "\nSoftware:\n"
            for s in software_hits:
                context += f"- {s.name}\n"

    except:
        context = ""

    # 🧠 SMART SYSTEM PROMPT
    system_prompt = f"""
You are a smart AI assistant for JMJ Softwares website.

Rules:
- Be helpful, short and clear
- Guide users to correct pages when needed
- Use simple English or Swahili if user uses Swahili
- Do NOT repeat same answers

Website sections:
- Tutorials: /tutorials/
- Software: /software/
- Livestreams: /livestreams/
- Contact: /contactus/

Context from website:
{context}
"""

    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ],
            "temperature": 0.7,
            "max_tokens": 500
        }

        resp = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=15
        )

        if resp.status_code == 200:
            result = resp.json()
            reply = result["choices"][0]["message"]["content"]

            return JsonResponse({
                "answer": reply
            })

        else:
            return JsonResponse({
                "answer": f"OpenAI error: {resp.status_code}"
            })

    except Exception as e:
        return JsonResponse({
            "answer": f"AI request failed: {str(e)}"
        })


def user_search(request):
    """Return JSON list of usernames matching query param `q` for autocomplete."""
    q = request.GET.get('q', '').strip()
    User = get_user_model()
    results = []
    if q:
        qs = User.objects.filter(username__icontains=q).order_by('username')[:12]
        results = [u.username for u in qs]
    return JsonResponse({'results': results})