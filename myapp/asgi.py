"""
ASGI config for myapp project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myapp.settings')

# Use Channels if available to support WebSocket protocol; otherwise fall back to default ASGI app
try:
	from channels.routing import ProtocolTypeRouter, URLRouter
	from channels.auth import AuthMiddlewareStack
	import accounts.routing

	django_asgi_app = get_asgi_application()

	application = ProtocolTypeRouter({
		"http": django_asgi_app,
		"websocket": AuthMiddlewareStack(
			URLRouter(
				accounts.routing.websocket_urlpatterns
			)
		),
	})
except Exception:
	application = get_asgi_application()
