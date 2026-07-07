from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase, override_settings

from apps.builder.models.pc_build import PCBuild, PCBuildOrder, PCComponent
from apps.chat.utils.send_mail import create_order, notify_admin_about_message, notify_user_about_order


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class NotifyAdminAboutMessageTest(TestCase):
    def test_sends_email_to_admin(self) -> None:
        with patch("django.template.loader.render_to_string", return_value="<p>body</p>"):
            notify_admin_about_message(
                user_email="user@example.com",
                username="alice",
                user_message="Hello",
            )
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("alice", mail.outbox[0].subject)

    def test_subject_contains_username(self) -> None:
        with patch("django.template.loader.render_to_string", return_value="<p>body</p>"):
            notify_admin_about_message("u@e.com", "bob", "Hi")
        self.assertIn("bob", mail.outbox[0].subject)


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class NotifyUserAboutOrderTest(TestCase):
    def setUp(self) -> None:
        user = User.objects.create_user(username="customer", password="pass", email="c@example.com")
        build = PCBuild.objects.create(name="Gaming Build")
        build.components.add(PCComponent.objects.create(name="GPU", price=Decimal("500.00")))
        self.order = PCBuildOrder.objects.create(build=build, customer=user)

    def test_delivery_notification_subject(self) -> None:
        with patch("django.template.loader.render_to_string", return_value="<p>body</p>"):
            notify_user_about_order("c@example.com", "customer", self.order, is_delivered=True)
        self.assertIn("delivered", mail.outbox[0].subject.lower())

    def test_completion_notification_subject(self) -> None:
        with patch("django.template.loader.render_to_string", return_value="<p>body</p>"):
            notify_user_about_order("c@example.com", "customer", self.order, is_delivered=False)
        self.assertIn("sent", mail.outbox[0].subject.lower())

    def test_email_sent_to_user(self) -> None:
        with patch("django.template.loader.render_to_string", return_value="<p>body</p>"):
            notify_user_about_order("c@example.com", "customer", self.order, is_delivered=False)
        self.assertEqual(mail.outbox[0].to, ["c@example.com"])


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class CreateOrderEmailTest(TestCase):
    def setUp(self) -> None:
        user = User.objects.create_user(username="customer", password="pass", email="c@example.com")
        build = PCBuild.objects.create(name="Budget Build")
        self.order = PCBuildOrder.objects.create(build=build, customer=user)

    def test_sends_order_confirmation_email(self) -> None:
        with patch("django.template.loader.render_to_string", return_value="<p>body</p>"):
            create_order("c@example.com", "customer", self.order)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["c@example.com"])
