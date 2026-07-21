from pathlib import Path
import dj_database_url
import os
from dotenv import load_dotenv
import cloudinary


# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env
load_dotenv(BASE_DIR / ".env")
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

# SECURITY
SECRET_KEY = os.getenv('SECRET_KEY')
DEBUG = os.getenv('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = [
    "joh-python.fly.dev",
    "johanes2005.onrender.com",
    "localhost",
    "127.0.0.1",
    ".fly.dev",
]
X_FRAME_OPTIONS = "ALLOWALL"
# OpenAI API Key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# SendGrid
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")

# Login redirects
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'login'

# INSTALLED APPS
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'accounts',
    'cloudinary',
    'cloudinary_storage',
]

# Channels (optional)
try:
    import channels  # noqa
    INSTALLED_APPS.append('channels')
except Exception:
    pass

# MIDDLEWARE
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'myapp.urls'

# TEMPLATES
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'accounts.context_processors.notifications_count',
            ],
        },
    },
]

WSGI_APPLICATION = 'myapp.wsgi.application'
ASGI_APPLICATION = 'myapp.asgi.application'

# DATABASE
DATABASES = {
    "default": dj_database_url.parse(
        os.environ.get(
            "DATABASE_URL",
            "sqlite:///db.sqlite3"
        ),
        conn_max_age=60,
        ssl_require=True
    )
}

# PASSWORD VALIDATION
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# INTERNATIONALIZATION
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# STATIC FILES
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / "staticfiles"

# MEDIA FILES
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# WhiteNoise storage
STORAGES = {
    "default": {
        "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CRISPY
CRISPY_TEMPLATE_PACK = 'bootstrap4'

# REDIS / CHANNELS

REDIS_URL = os.getenv("REDIS_URL")
CHANNEL_LAYERS = {
"default": {
"BACKEND": "channels_redis.core.RedisChannelLayer",
"CONFIG": {
"hosts": [
{
"address": REDIS_URL,
"ssl": True,
}
],
"capacity":1500,
"expiry":120,
},
},
}

MEDIA_URL = '/media/'


# CSRF SETTINGS
CSRF_TRUSTED_ORIGINS = [
    "https://johanes2005.onrender.com",
    "https://joh-python.fly.dev",
    "http://localhost:8001",
    "http://127.0.0.1:8001",
]
# SECURITY SETTINGS
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_SSL_REDIRECT = False
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")