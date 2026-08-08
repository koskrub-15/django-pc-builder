"""ASGI entry point: plain HTTP plus the authenticated WebSocket router.

Exposes the ASGI callable as a module-level variable named ``application``.
Daphne serves this; Gunicorn serves core.wsgi for HTTP only.
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

# Must be initialised before the routing module imports any model.
django_asgi_app = get_asgi_application()

from apps.chat import routing  # noqa: E402

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": AllowedHostsOriginValidator(
            AuthMiddlewareStack(
                URLRouter(
                    routing.websocket_urlpatterns,
                ),
            ),
        ),
    },
)
