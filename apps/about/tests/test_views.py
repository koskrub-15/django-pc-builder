from unittest.mock import Mock, patch

from django.core import mail
from django.test import TestCase
from django.urls import reverse

VALID = {"name": "Ada", "email": "ada@example.com", "message": "I want a build."}

OWNER = {
    "name": "Test Owner",
    "role": "Backend Developer",
    "bio": "Builds things.",
    "github": "https://github.com/example",
    "telegram": "https://t.me/example",
    "linkedin": "https://linkedin.com/in/example",
    "email": "owner@example.com",
}
BLANK_OWNER = dict.fromkeys(OWNER, "")


class AboutIndexViewTest(TestCase):
    def test_returns_200(self) -> None:
        response = self.client.get(reverse("about:index"))
        self.assertEqual(response.status_code, 200)

    def test_uses_about_template(self) -> None:
        response = self.client.get(reverse("about:index"))
        self.assertTemplateUsed(response, "about/index.html")

    def test_contact_form_is_rendered(self) -> None:
        response = self.client.get(reverse("about:index"))
        self.assertContains(response, 'name="message"')
        self.assertContains(response, "csrfmiddlewaretoken")


class AboutOwnerSectionTest(TestCase):
    """Owner details are configuration, never committed content."""

    def test_owner_sections_are_hidden_when_unset(self) -> None:
        with self.settings(SITE_OWNER=BLANK_OWNER):
            response = self.client.get(reverse("about:index"))
        self.assertNotContains(response, "Elsewhere")

    def test_owner_details_are_shown_when_configured(self) -> None:
        with self.settings(SITE_OWNER=OWNER):
            response = self.client.get(reverse("about:index"))
        self.assertContains(response, "Test Owner")
        self.assertContains(response, "Backend Developer")
        self.assertContains(response, "https://github.com/example")
        self.assertContains(response, "mailto:owner@example.com")

    def test_contact_form_is_shown_even_without_an_owner(self) -> None:
        with self.settings(SITE_OWNER=BLANK_OWNER):
            response = self.client.get(reverse("about:index"))
        self.assertContains(response, "Get in touch")


class ContactFormSubmissionTest(TestCase):
    def test_valid_submission_redirects_back(self) -> None:
        response = self.client.post(reverse("about:index"), VALID)
        self.assertRedirects(response, reverse("about:index"))

    def test_valid_submission_sends_an_email(self) -> None:
        self.client.post(reverse("about:index"), VALID)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Ada", mail.outbox[0].subject)

    def test_email_replies_go_to_the_visitor(self) -> None:
        self.client.post(reverse("about:index"), VALID)
        self.assertEqual(mail.outbox[0].reply_to, ["ada@example.com"])

    def test_email_body_carries_the_message(self) -> None:
        self.client.post(reverse("about:index"), VALID)
        self.assertIn("I want a build.", mail.outbox[0].body)

    def test_success_message_is_shown_after_redirect(self) -> None:
        response = self.client.post(reverse("about:index"), VALID, follow=True)
        self.assertContains(response, "Your message has been sent")

    def test_invalid_submission_sends_nothing(self) -> None:
        response = self.client.post(reverse("about:index"), {**VALID, "email": "nope"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 0)

    def test_invalid_submission_redisplays_errors(self) -> None:
        response = self.client.post(reverse("about:index"), {**VALID, "email": "nope"})
        self.assertTrue(response.context["form"].errors)

    def test_submitted_content_is_escaped_on_redisplay(self) -> None:
        response = self.client.post(
            reverse("about:index"),
            {**VALID, "email": "nope", "name": "<script>alert(1)</script>"},
        )
        body = response.content.decode()
        self.assertNotIn("<script>alert(1)</script>", body)

    @patch("apps.about.views.send_contact_message")
    def test_view_passes_cleaned_data_to_the_mailer(self, mock_send: Mock) -> None:
        self.client.post(reverse("about:index"), {**VALID, "message": "  spaced  "})
        mock_send.assert_called_once_with(name="Ada", email="ada@example.com", message="spaced")
