"""WebSocket routes, mounted by the ASGI application in core/asgi.py."""

from django.urls import path

from . import consumers

websocket_urlpatterns = [
    path("ws/chat/<int:thread_id>/", consumers.ChatConsumer.as_asgi()),
]
