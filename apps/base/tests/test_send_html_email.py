import logging
from unittest.mock import patch

from django.core import mail
from django.test import TestCase, override_settings

from apps.base.utils.send_html_email import send_html_email


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class SendHtmlEmailTest(TestCase):
    def _send(self) -> bool:
        with patch("django.template.loader.render_to_string", return_value="<p>body</p>"):
            return send_html_email(
                subject="Subject",
                template_name="email/admin_message.html",
                context={},
                recipients=["someone@example.com"],
            )

    def test_successful_send_reports_true(self) -> None:
        self.assertTrue(self._send())
        self.assertEqual(len(mail.outbox), 1)

    def test_reply_to_is_applied_when_given(self) -> None:
        with patch("django.template.loader.render_to_string", return_value="<p>body</p>"):
            send_html_email(
                subject="Subject",
                template_name="email/admin_message.html",
                context={},
                recipients=["owner@example.com"],
                reply_to=["visitor@example.com"],
            )
        self.assertEqual(mail.outbox[0].reply_to, ["visitor@example.com"])

    def test_smtp_failure_is_reported_and_not_raised(self) -> None:
        with (
            patch(
                "django.core.mail.EmailMultiAlternatives.send",
                side_effect=ConnectionRefusedError("no mail server"),
            ),
            self.assertLogs("apps.base.utils.send_html_email", level=logging.ERROR) as logs,
        ):
            sent = self._send()

        self.assertFalse(sent)
        self.assertEqual(len(mail.outbox), 0)
        self.assertIn("Could not send email", logs.output[0])

    def test_successful_send_is_logged_once(self) -> None:
        with self.assertLogs("apps.base.utils.send_html_email", level=logging.INFO) as logs:
            self._send()

        self.assertEqual(len(logs.output), 1)
        self.assertIn("Sent email", logs.output[0])
