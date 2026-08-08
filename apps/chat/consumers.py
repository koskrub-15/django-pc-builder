"""WebSocket consumer that streams a chat thread to its participants."""

import json
import logging
from typing import Any

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import AbstractBaseUser, AnonymousUser

from .models import ChatMessage, ChatThread
from .utils.access import may_access_thread

logger = logging.getLogger(__name__)

# Application-defined close codes (the 4000-4999 range is reserved for apps).
WS_CLOSE_UNAUTHENTICATED = 4401
WS_CLOSE_FORBIDDEN = 4403


class ChatConsumer(AsyncWebsocketConsumer):
    """Broadcasts messages of a single thread to everyone allowed to read it."""

    async def connect(self) -> None:
        """Join the thread group, rejecting anyone who may not read the thread."""
        thread_id = self.scope["url_route"]["kwargs"]["thread_id"]
        user = self.scope.get("user")

        if user is None or user.is_anonymous:
            await self.close(code=WS_CLOSE_UNAUTHENTICATED)
            return

        thread = await self.get_accessible_thread(user, thread_id)
        if thread is None:
            await self.close(code=WS_CLOSE_FORBIDDEN)
            return

        # Resolved once at connect time so every inbound message is a single
        # write instead of re-loading the sender and the thread each time.
        self.user = user
        self.thread = thread
        self.room_group_name = f"chat_{thread_id}"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        await self.send(
            text_data=json.dumps(
                {
                    "message": "Chat connection established",
                    "sender": "System",
                },
            ),
        )

    async def disconnect(self, close_code: int) -> None:  # noqa: ARG002
        """Leave the thread group, if the socket ever joined one."""
        # A socket rejected in connect() never joined a group but still gets here.
        group_name = getattr(self, "room_group_name", None)
        if group_name is not None:
            await self.channel_layer.group_discard(group_name, self.channel_name)

    async def receive(self, text_data: str) -> None:
        """Persist an inbound message and fan it out to the thread group."""
        try:
            data = json.loads(text_data)
            message = str(data["message"]).strip()
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            await self._send_system_message(f"Invalid message format: {e!s}")
            logger.exception("Message format error")
            return

        if not message:
            return

        try:
            await self.save_message(self.thread, self.user, message)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message",
                    "message": message,
                    "sender": self.user.get_username(),
                    "is_html": False,
                },
            )
        except Exception:
            await self._send_system_message("An unexpected error occurred")
            logger.exception("Unexpected error in chat consumer")

    async def chat_message(self, event: dict[str, Any]) -> None:
        """Forward a group broadcast to this socket."""
        await self.send(
            text_data=json.dumps(
                {
                    "message": event["message"],
                    "sender": event["sender"],
                    "is_html": event.get("is_html", False),
                },
            ),
        )

    async def _send_system_message(self, message: str) -> None:
        """Send an out-of-band notice attributed to "System"."""
        await self.send(text_data=json.dumps({"message": message, "sender": "System"}))

    @database_sync_to_async
    def get_accessible_thread(
        self,
        user: AbstractBaseUser | AnonymousUser,
        thread_id: int,
    ) -> ChatThread | None:
        """Return the thread if the user may read it, otherwise None."""
        thread = ChatThread.objects.filter(id=thread_id).first()
        if thread is None or not may_access_thread(user, thread):
            return None
        return thread

    @database_sync_to_async
    def save_message(self, thread: ChatThread, sender: AbstractBaseUser, text: str) -> ChatMessage:
        """Store an inbound message as plain text (never as trusted markup)."""
        return ChatMessage.objects.create(thread=thread, sender=sender, text=text)
