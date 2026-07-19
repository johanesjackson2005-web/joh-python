import os

from django.core.asgi import get_asgi_application

os.environ.setdefault(
    'DJANGO_SETTINGS_MODULE',
    'myapp.settings'
)

django_asgi_app = get_asgi_application()


try:
    from channels.auth import AuthMiddlewareStack
    from channels.routing import ProtocolTypeRouter, URLRouter
    from accounts.routing import websocket_urlpatterns

    application = ProtocolTypeRouter({
        "http": django_asgi_app,
        "websocket": AuthMiddlewareStack(
            URLRouter(
                websocket_urlpatterns
            )
        ),
    })

except ImportError:
    application = django_asgi_app