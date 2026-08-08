from django.contrib.auth.models import User
from django.test import TestCase

from apps.chat.models import ChatMessage, ChatThread


class ChatThreadModelTest(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username="alice", password="pass")
        self.thread = ChatThread.objects.create(user=self.user)

    def test_str_contains_username(self) -> None:
        self.assertIn("alice", str(self.thread))

    def test_str_contains_thread_id(self) -> None:
        self.assertIn(str(self.thread.id), str(self.thread))


class ChatMessageModelTest(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username="bob", password="pass")
        thread = ChatThread.objects.create(user=self.user)
        self.message = ChatMessage.objects.create(thread=thread, sender=self.user, text="Hello")

    def test_str_contains_sender_username(self) -> None:
        self.assertIn("bob", str(self.message))
