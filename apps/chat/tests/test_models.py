from django.contrib.auth.models import User
from django.db.utils import IntegrityError
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


class ChatThreadConstraintTest(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username="carol", password="pass")

    def test_a_user_cannot_have_two_threads(self) -> None:
        ChatThread.objects.create(user=self.user)
        with self.assertRaises(IntegrityError):
            ChatThread.objects.create(user=self.user)

    def test_thread_is_reachable_from_the_user(self) -> None:
        thread = ChatThread.objects.create(user=self.user)
        self.assertEqual(self.user.chat_thread, thread)


class ChatMessageOrderingTest(TestCase):
    def test_messages_come_back_oldest_first(self) -> None:
        user = User.objects.create_user(username="dave", password="pass")
        thread = ChatThread.objects.create(user=user)
        first = ChatMessage.objects.create(thread=thread, sender=user, text="first")
        second = ChatMessage.objects.create(thread=thread, sender=user, text="second")

        self.assertEqual(list(thread.messages.all()), [first, second])
