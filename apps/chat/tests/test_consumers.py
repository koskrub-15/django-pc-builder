import json
from unittest.mock import patch

from channels.db import database_sync_to_async
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator
from django.contrib.auth.models import AnonymousUser, User
from django.test import TestCase

from apps.chat import routing
from apps.chat.consumers import ChatConsumer
from apps.chat.models import ChatMessage, ChatThread

application = URLRouter(routing.websocket_urlpatterns)


class ChatConsumerConnectTest(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username="alice", password="pass")
        self.thread = ChatThread.objects.create(user=self.user)

    async def test_connect_accepts_and_sends_system_message(self) -> None:
        communicator = WebsocketCommunicator(application, f"/ws/chat/{self.thread.id}/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        response = await communicator.receive_json_from()
        self.assertEqual(response["sender"], "System")
        await communicator.disconnect()

    async def test_disconnect_does_not_raise(self) -> None:
        communicator = WebsocketCommunicator(application, f"/ws/chat/{self.thread.id}/")
        await communicator.connect()
        await communicator.receive_json_from()
        await communicator.disconnect()


class ChatConsumerReceiveTest(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username="alice", password="pass")
        self.thread = ChatThread.objects.create(user=self.user)

    async def _connected_communicator(self, user: User | AnonymousUser) -> WebsocketCommunicator:
        communicator = WebsocketCommunicator(application, f"/ws/chat/{self.thread.id}/")
        communicator.scope["user"] = user
        await communicator.connect()
        await communicator.receive_json_from()
        return communicator

    async def test_authenticated_user_message_is_saved_and_broadcast(self) -> None:
        communicator = await self._connected_communicator(self.user)

        await communicator.send_json_to({"message": "Hello admin"})
        response = await communicator.receive_json_from()

        self.assertEqual(response["message"], "Hello admin")
        self.assertEqual(response["sender"], "alice")
        saved = await self._get_last_message()
        self.assertEqual(saved.text, "Hello admin")
        self.assertEqual(saved.sender_id, self.user.id)

        await communicator.disconnect()

    async def test_message_broadcasts_to_other_connected_client(self) -> None:
        sender_comm = await self._connected_communicator(self.user)
        listener_comm = await self._connected_communicator(self.user)

        await sender_comm.send_json_to({"message": "Broadcast me"})

        sender_response = await sender_comm.receive_json_from()
        listener_response = await listener_comm.receive_json_from()
        self.assertEqual(sender_response["message"], "Broadcast me")
        self.assertEqual(listener_response["message"], "Broadcast me")

        await sender_comm.disconnect()
        await listener_comm.disconnect()

    async def test_anonymous_user_gets_auth_error(self) -> None:
        communicator = await self._connected_communicator(AnonymousUser())

        await communicator.send_json_to({"message": "Hello"})
        response = await communicator.receive_json_from()

        self.assertEqual(response["sender"], "System")
        self.assertIn("authenticated", response["message"])
        self.assertEqual(await self._message_count(), 0)

        await communicator.disconnect()

    async def test_invalid_json_returns_error_message(self) -> None:
        communicator = await self._connected_communicator(self.user)

        await communicator.send_to(text_data="not-json")
        response = await communicator.receive_json_from()

        self.assertEqual(response["sender"], "System")
        self.assertIn("Invalid message format", response["message"])

        await communicator.disconnect()

    async def test_missing_message_key_returns_error(self) -> None:
        communicator = await self._connected_communicator(self.user)

        await communicator.send_to(text_data=json.dumps({"not_message": "oops"}))
        response = await communicator.receive_json_from()

        self.assertEqual(response["sender"], "System")
        self.assertIn("Invalid message format", response["message"])

        await communicator.disconnect()

    async def test_broadcast_marks_user_messages_as_non_html(self) -> None:
        communicator = await self._connected_communicator(self.user)

        await communicator.send_json_to({"message": "<b>not bold</b>"})
        response = await communicator.receive_json_from()

        self.assertFalse(response["is_html"])
        self.assertEqual(response["message"], "<b>not bold</b>")

        await communicator.disconnect()

    async def test_unknown_user_reports_database_error(self) -> None:
        # An unsaved User instance is not anonymous, so the consumer gets past the
        # auth check and then fails to load the sender row.
        communicator = await self._connected_communicator(User(id=999999, username="ghost"))

        await communicator.send_json_to({"message": "Hello"})
        response = await communicator.receive_json_from()

        self.assertEqual(response["sender"], "System")
        self.assertIn("Database error", response["message"])
        self.assertEqual(await self._message_count(), 0)

        await communicator.disconnect()

    async def test_unexpected_error_is_reported_to_the_client(self) -> None:
        communicator = await self._connected_communicator(self.user)

        with patch.object(ChatConsumer, "save_message", side_effect=RuntimeError("boom")):
            await communicator.send_json_to({"message": "Hello"})
            response = await communicator.receive_json_from()

        self.assertEqual(response["sender"], "System")
        self.assertIn("unexpected error", response["message"])

        await communicator.disconnect()

    async def _get_last_message(self) -> ChatMessage:
        return await database_sync_to_async(ChatMessage.objects.latest)("id")

    async def _message_count(self) -> int:
        return await database_sync_to_async(ChatMessage.objects.count)()
