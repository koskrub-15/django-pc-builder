import json
import logging
from typing import Any

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import User

from .models import ChatMessage, ChatThread

logger = logging.getLogger(__name__)


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self) -> None:
        self.thread_id = self.scope["url_route"]["kwargs"]["thread_id"]
        self.room_group_name = f"chat_{self.thread_id}"

        # Add user to chat group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        # Send connection confirmation
        await self.send(
            text_data=json.dumps(
                {
                    "message": "Chat connection established",
                    "sender": "System",
                },
            ),
        )

    async def disconnect(self, close_code: int) -> None:  # noqa: ARG002
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data: str) -> None:
        try:
            data = json.loads(text_data)
            message = data["message"]

            # Check if user is authenticated
            if self.scope["user"].is_anonymous:
                await self.send(
                    text_data=json.dumps(
                        {
                            "message": "You must be authenticated to send messages",
                            "sender": "System",
                        },
                    ),
                )
                return

            user_id = self.scope["user"].id
            sender = await self.get_user(user_id)
            thread = await self.get_thread()

            # Save message to database
            await self.save_message(thread, sender, message)

            # Send message to all participants in the group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message",
                    "message": message,
                    "sender": sender.username,
                },
            )
        except (json.JSONDecodeError, KeyError) as e:
            # Send error message to sender for specific JSON/Key errors
            await self.send(
                text_data=json.dumps(
                    {
                        "message": f"Invalid message format: {e!s}",
                        "sender": "System",
                    },
                ),
            )
            logger.exception("Message format error")
        except (User.DoesNotExist, ChatThread.DoesNotExist):
            # Send error message for database errors
            await self.send(
                text_data=json.dumps(
                    {
                        "message": "Database error occurred",
                        "sender": "System",
                    },
                ),
            )
            logger.exception("Database error")
        except Exception:
            # Send error message to sender for unexpected errors
            await self.send(
                text_data=json.dumps(
                    {
                        "message": "An unexpected error occurred",
                        "sender": "System",
                    },
                ),
            )
            logger.exception("Unexpected error in chat consumer")

    async def chat_message(self, event: dict[str, Any]) -> None:
        # Send message to WebSocket
        await self.send(
            text_data=json.dumps(
                {
                    "message": event["message"],
                    "sender": event["sender"],
                },
            ),
        )

    @database_sync_to_async
    def get_user(self, user_id: int) -> User:
        return User.objects.get(id=user_id)

    @database_sync_to_async
    def get_thread(self) -> ChatThread:
        return ChatThread.objects.get(id=self.thread_id)

    @database_sync_to_async
    def save_message(self, thread: ChatThread, sender: User, text: str) -> ChatMessage:
        return ChatMessage.objects.create(thread=thread, sender=sender, text=text)
