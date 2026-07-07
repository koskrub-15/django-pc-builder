import json
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from apps.chat.models import ChatMessage, ChatThread


class ContactAdminViewTest(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username="user", password="pass")

    def test_redirects_anonymous(self) -> None:
        response = self.client.get(reverse("chat:contact_admin"))
        self.assertEqual(response.status_code, 302)

    def test_creates_thread_on_first_visit(self) -> None:
        self.client.login(username="user", password="pass")
        self.client.get(reverse("chat:contact_admin"))
        self.assertTrue(ChatThread.objects.filter(user=self.user).exists())

    def test_reuses_existing_thread(self) -> None:
        thread = ChatThread.objects.create(user=self.user)
        self.client.login(username="user", password="pass")
        self.client.get(reverse("chat:contact_admin"))
        self.assertEqual(ChatThread.objects.filter(user=self.user).count(), 1)
        self.assertEqual(ChatThread.objects.get(user=self.user), thread)


class GetMessagesViewTest(TestCase):
    def setUp(self) -> None:
        self.owner = User.objects.create_user(username="owner", password="pass")
        self.staff = User.objects.create_user(username="staff", password="pass", is_staff=True)
        self.other = User.objects.create_user(username="other", password="pass")
        self.thread = ChatThread.objects.create(user=self.owner)
        ChatMessage.objects.create(thread=self.thread, sender=self.owner, text="Hello")

    def test_owner_can_get_messages(self) -> None:
        self.client.login(username="owner", password="pass")
        response = self.client.get(reverse("chat:get_messages", args=[self.thread.id]))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data["messages"]), 1)
        self.assertEqual(data["messages"][0]["text"], "Hello")

    def test_staff_can_get_any_thread_messages(self) -> None:
        self.client.login(username="staff", password="pass")
        response = self.client.get(reverse("chat:get_messages", args=[self.thread.id]))
        self.assertEqual(response.status_code, 200)

    def test_other_user_gets_403(self) -> None:
        self.client.login(username="other", password="pass")
        response = self.client.get(reverse("chat:get_messages", args=[self.thread.id]))
        self.assertEqual(response.status_code, 403)

    def test_only_new_messages_filter(self) -> None:
        msg2 = ChatMessage.objects.create(thread=self.thread, sender=self.owner, text="Second")
        self.client.login(username="owner", password="pass")
        first_id = ChatMessage.objects.first().id
        response = self.client.get(
            reverse("chat:get_messages", args=[self.thread.id]),
            {"only_new": "true", "last_id": str(first_id)},
        )
        data = json.loads(response.content)
        self.assertEqual(len(data["messages"]), 1)
        self.assertEqual(data["messages"][0]["id"], msg2.id)

    def test_anonymous_redirects(self) -> None:
        response = self.client.get(reverse("chat:get_messages", args=[self.thread.id]))
        self.assertEqual(response.status_code, 302)


class SendMessageViewTest(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username="user", password="pass", email="u@example.com")
        self.thread = ChatThread.objects.create(user=self.user)
        self.client.login(username="user", password="pass")

    @patch("apps.chat.views.notify_admin_about_message")
    def test_post_creates_message(self, mock_notify: object) -> None:
        self.client.post(
            reverse("chat:send_message", args=[self.thread.id]),
            {"message": "Hello admin"},
        )
        self.assertEqual(ChatMessage.objects.filter(thread=self.thread).count(), 1)

    @patch("apps.chat.views.notify_admin_about_message")
    def test_empty_message_is_ignored(self, mock_notify: object) -> None:
        self.client.post(
            reverse("chat:send_message", args=[self.thread.id]),
            {"message": "   "},
        )
        self.assertEqual(ChatMessage.objects.filter(thread=self.thread).count(), 0)

    @patch("apps.chat.views.notify_admin_about_message")
    def test_first_message_notifies_admin(self, mock_notify: object) -> None:
        self.client.post(
            reverse("chat:send_message", args=[self.thread.id]),
            {"message": "Need help"},
        )
        mock_notify.assert_called_once()

    def test_staff_message_does_not_notify_admin(self) -> None:
        staff = User.objects.create_user(username="staff", password="pass", is_staff=True)
        self.client.login(username="staff", password="pass")
        with patch("apps.chat.views.notify_admin_about_message") as mock_notify:
            self.client.post(
                reverse("chat:send_message", args=[self.thread.id]),
                {"message": "Staff reply"},
            )
            mock_notify.assert_not_called()


class ThreadListViewTest(TestCase):
    def setUp(self) -> None:
        self.staff = User.objects.create_user(username="staff", password="pass", is_staff=True)
        self.user = User.objects.create_user(username="user", password="pass")

    def test_staff_can_see_thread_list(self) -> None:
        self.client.login(username="staff", password="pass")
        response = self.client.get(reverse("chat:thread_list"))
        self.assertEqual(response.status_code, 200)

    def test_regular_user_is_redirected(self) -> None:
        self.client.login(username="user", password="pass")
        response = self.client.get(reverse("chat:thread_list"))
        self.assertEqual(response.status_code, 302)
