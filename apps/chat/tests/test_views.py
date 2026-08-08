import json
from decimal import Decimal
from unittest.mock import Mock, patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from apps.builder.models.pc_build import OrderProgress, PCBuild, PCBuildOrder, PCComponent
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

    def test_non_numeric_last_id_is_ignored(self) -> None:
        self.client.login(username="owner", password="pass")
        response = self.client.get(
            reverse("chat:get_messages", args=[self.thread.id]),
            {"only_new": "true", "last_id": "abc"},
        )
        data = json.loads(response.content)
        self.assertEqual(len(data["messages"]), 1)


class SendMessageViewTest(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username="user", password="pass", email="u@example.com")
        self.thread = ChatThread.objects.create(user=self.user)
        self.client.login(username="user", password="pass")

    @patch("apps.chat.views.async_to_sync")
    @patch("apps.chat.views.notify_admin_about_message")
    def test_post_creates_message(self, _mock_notify: object, _mock_async: object) -> None:
        self.client.post(
            reverse("chat:send_message", args=[self.thread.id]),
            {"message": "Hello admin"},
        )
        self.assertEqual(ChatMessage.objects.filter(thread=self.thread).count(), 1)

    @patch("apps.chat.views.async_to_sync")
    @patch("apps.chat.views.notify_admin_about_message")
    def test_empty_message_is_ignored(self, _mock_notify: object, _mock_async: object) -> None:
        self.client.post(
            reverse("chat:send_message", args=[self.thread.id]),
            {"message": "   "},
        )
        self.assertEqual(ChatMessage.objects.filter(thread=self.thread).count(), 0)

    @patch("apps.chat.views.async_to_sync")
    @patch("apps.chat.views.notify_admin_about_message")
    def test_first_message_notifies_admin(self, mock_notify: Mock, _mock_async: object) -> None:
        self.client.post(
            reverse("chat:send_message", args=[self.thread.id]),
            {"message": "Need help"},
        )
        mock_notify.assert_called_once()

    @patch("apps.chat.views.async_to_sync")
    def test_staff_message_does_not_notify_admin(self, _mock_async: object) -> None:
        User.objects.create_user(username="staff", password="pass", is_staff=True)
        self.client.login(username="staff", password="pass")
        with patch("apps.chat.views.notify_admin_about_message") as mock_notify:
            self.client.post(
                reverse("chat:send_message", args=[self.thread.id]),
                {"message": "Staff reply"},
            )
            mock_notify.assert_not_called()

    @patch("apps.chat.views.async_to_sync")
    @patch("apps.chat.views.notify_admin_about_message")
    def test_ajax_request_returns_204(self, _mock_notify: object, _mock_async: object) -> None:
        response = self.client.post(
            reverse("chat:send_message", args=[self.thread.id]),
            {"message": "Hello"},
            headers={"x-requested-with": "XMLHttpRequest"},
        )
        self.assertEqual(response.status_code, 204)

    @patch("apps.chat.views.async_to_sync")
    @patch("apps.chat.views.notify_admin_about_message")
    def test_normal_request_redirects(self, _mock_notify: object, _mock_async: object) -> None:
        response = self.client.post(
            reverse("chat:send_message", args=[self.thread.id]),
            {"message": "Hello"},
        )
        self.assertEqual(response.status_code, 302)


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


class ChatRoomViewTest(TestCase):
    def setUp(self) -> None:
        self.owner = User.objects.create_user(username="owner", password="pass")
        self.staff = User.objects.create_user(username="staff", password="pass", is_staff=True)
        self.thread = ChatThread.objects.create(user=self.owner)
        ChatMessage.objects.create(thread=self.thread, sender=self.owner, text="Hello")

    def test_anonymous_is_redirected(self) -> None:
        response = self.client.get(reverse("chat:chat_room", args=[self.thread.id]))
        self.assertEqual(response.status_code, 302)

    def test_owner_sees_messages(self) -> None:
        self.client.login(username="owner", password="pass")
        response = self.client.get(reverse("chat:chat_room", args=[self.thread.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["chat_messages"]), 1)

    def test_regular_user_gets_no_build_picker(self) -> None:
        self.client.login(username="owner", password="pass")
        response = self.client.get(reverse("chat:chat_room", args=[self.thread.id]))
        self.assertNotIn("builds", response.context)

    def test_staff_gets_build_picker(self) -> None:
        PCBuild.objects.create(name="Gaming Build")
        self.client.login(username="staff", password="pass")
        response = self.client.get(reverse("chat:chat_room", args=[self.thread.id]))
        self.assertEqual(len(response.context["builds"]), 1)

    def test_missing_thread_returns_404(self) -> None:
        self.client.login(username="owner", password="pass")
        response = self.client.get(reverse("chat:chat_room", args=[99999]))
        self.assertEqual(response.status_code, 404)


class CreateOrderFromChatTest(TestCase):
    def setUp(self) -> None:
        self.customer = User.objects.create_user(username="customer", password="pass", email="c@example.com")
        self.staff = User.objects.create_user(username="staff", password="pass", is_staff=True)
        self.thread = ChatThread.objects.create(user=self.customer)
        self.build = PCBuild.objects.create(name="Gaming Build")
        self.component = PCComponent.objects.create(name="RTX 5090", price=Decimal("2000.00"))
        self.build.components.add(self.component)
        self.url = reverse("chat:create_order_from_chat", args=[self.thread.id])

    def test_regular_user_cannot_create_order(self) -> None:
        self.client.login(username="customer", password="pass")
        response = self.client.post(self.url, {"build_id": str(self.build.id)})
        self.assertRedirects(response, reverse("chat:chat_room", args=[self.thread.id]))
        self.assertEqual(PCBuildOrder.objects.count(), 0)

    @patch("apps.chat.views.create_order")
    def test_staff_creates_order_with_progress(self, mock_create_order: Mock) -> None:
        self.client.login(username="staff", password="pass")
        self.client.post(self.url, {"build_id": str(self.build.id), "address": "Main St 1", "markup": "10.50"})

        order = PCBuildOrder.objects.get()
        self.assertEqual(order.customer, self.customer)
        self.assertEqual(order.address, "Main St 1")
        self.assertEqual(order.markup, Decimal("10.50"))
        self.assertTrue(OrderProgress.objects.filter(order=order).exists())
        mock_create_order.assert_called_once()

    @patch("apps.chat.views.create_order")
    def test_invalid_markup_falls_back_to_zero(self, _mock_create_order: Mock) -> None:
        self.client.login(username="staff", password="pass")
        self.client.post(self.url, {"build_id": str(self.build.id), "markup": "not-a-number"})
        self.assertEqual(PCBuildOrder.objects.get().markup, Decimal("0.00"))

    @patch("apps.chat.views.create_order")
    def test_order_summary_is_posted_to_the_chat(self, _mock_create_order: Mock) -> None:
        self.client.login(username="staff", password="pass")
        self.client.post(self.url, {"build_id": str(self.build.id), "address": "Main St 1"})

        message = ChatMessage.objects.get(thread=self.thread)
        self.assertEqual(message.sender, self.staff)
        self.assertIn("Gaming Build", message.text)
        self.assertIn("RTX 5090", message.text)

    @patch("apps.chat.views.create_order")
    def test_unknown_build_returns_404(self, _mock_create_order: Mock) -> None:
        self.client.login(username="staff", password="pass")
        response = self.client.post(self.url, {"build_id": "99999"})
        self.assertEqual(response.status_code, 404)
        self.assertEqual(PCBuildOrder.objects.count(), 0)


class SendComponentListTest(TestCase):
    def setUp(self) -> None:
        self.customer = User.objects.create_user(username="customer", password="pass")
        self.staff = User.objects.create_user(username="staff", password="pass", is_staff=True)
        self.thread = ChatThread.objects.create(user=self.customer)
        self.build = PCBuild.objects.create(name="Office Build")
        self.build.components.add(PCComponent.objects.create(name="i5 CPU", price=Decimal("300.00")))
        self.url = reverse("chat:send_component_list", args=[self.thread.id])

    def test_regular_user_cannot_send_component_list(self) -> None:
        self.client.login(username="customer", password="pass")
        response = self.client.post(self.url, {"build_id": str(self.build.id)})
        self.assertRedirects(response, reverse("chat:chat_room", args=[self.thread.id]))
        self.assertEqual(ChatMessage.objects.count(), 0)

    def test_staff_posts_component_breakdown(self) -> None:
        self.client.login(username="staff", password="pass")
        response = self.client.post(self.url, {"build_id": str(self.build.id), "service_fee": "50.00"})

        self.assertRedirects(response, reverse("chat:chat_room", args=[self.thread.id]))
        message = ChatMessage.objects.get(thread=self.thread)
        self.assertIn("Office Build", message.text)
        self.assertIn("i5 CPU", message.text)
        self.assertIn("50.00", message.text)

    def test_invalid_service_fee_falls_back_to_zero(self) -> None:
        self.client.login(username="staff", password="pass")
        self.client.post(self.url, {"build_id": str(self.build.id), "service_fee": "free"})
        self.assertIn("Service fee: <b>0.00", ChatMessage.objects.get(thread=self.thread).text)

    def test_get_request_sends_nothing(self) -> None:
        self.client.login(username="staff", password="pass")
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse("chat:chat_room", args=[self.thread.id]))
        self.assertEqual(ChatMessage.objects.count(), 0)

    def test_unknown_build_returns_404(self) -> None:
        self.client.login(username="staff", password="pass")
        response = self.client.post(self.url, {"build_id": "99999"})
        self.assertEqual(response.status_code, 404)

    def test_component_names_are_escaped_in_the_generated_table(self) -> None:
        self.build.components.add(PCComponent.objects.create(name="<script>x</script>", price=Decimal("1.00")))
        self.client.login(username="staff", password="pass")
        self.client.post(self.url, {"build_id": str(self.build.id)})

        text = ChatMessage.objects.get(thread=self.thread).text
        self.assertNotIn("<script>", text)
        self.assertIn("&lt;script&gt;", text)


class ChatMessageEscapingTest(TestCase):
    """User-typed messages must never reach the page as markup."""

    def setUp(self) -> None:
        self.user = User.objects.create_user(username="user", password="pass", email="u@example.com")
        self.thread = ChatThread.objects.create(user=self.user)
        self.client.login(username="user", password="pass")

    @patch("apps.chat.views.async_to_sync")
    @patch("apps.chat.views.notify_admin_about_message")
    def test_user_message_is_stored_as_plain_text(self, _notify: object, _async: object) -> None:
        self.client.post(
            reverse("chat:send_message", args=[self.thread.id]),
            {"message": "<img src=x onerror=alert(1)>"},
        )
        message = ChatMessage.objects.get(thread=self.thread)
        self.assertFalse(message.is_html)

    @patch("apps.chat.views.async_to_sync")
    @patch("apps.chat.views.notify_admin_about_message")
    def test_user_message_is_escaped_when_rendered(self, _notify: object, _async: object) -> None:
        self.client.post(
            reverse("chat:send_message", args=[self.thread.id]),
            {"message": "<img src=x onerror=alert(1)>"},
        )
        response = self.client.get(reverse("chat:chat_room", args=[self.thread.id]))
        body = response.content.decode()
        self.assertNotIn("<img src=x onerror=alert(1)>", body)
        self.assertIn("&lt;img src=x onerror=alert(1)&gt;", body)

    def test_app_composed_message_is_rendered_as_markup(self) -> None:
        ChatMessage.objects.create(
            thread=self.thread,
            sender=self.user,
            text="<b>Order #1</b>",
            is_html=True,
        )
        response = self.client.get(reverse("chat:chat_room", args=[self.thread.id]))
        self.assertIn("<b>Order #1</b>", response.content.decode())
