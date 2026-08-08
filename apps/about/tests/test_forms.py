from django.test import TestCase

from apps.about.forms import ContactForm

VALID = {"name": "Ada", "email": "ada@example.com", "message": "I want a build."}


class ContactFormTest(TestCase):
    def test_valid_data_is_accepted(self) -> None:
        self.assertTrue(ContactForm(data=VALID).is_valid())

    def test_name_is_required(self) -> None:
        form = ContactForm(data={**VALID, "name": ""})
        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)

    def test_malformed_email_is_rejected(self) -> None:
        form = ContactForm(data={**VALID, "email": "not-an-email"})
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_whitespace_only_message_is_rejected(self) -> None:
        form = ContactForm(data={**VALID, "message": "     "})
        self.assertFalse(form.is_valid())
        self.assertIn("message", form.errors)

    def test_message_is_stripped(self) -> None:
        form = ContactForm(data={**VALID, "message": "  hello  "})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["message"], "hello")

    def test_overlong_message_is_rejected(self) -> None:
        form = ContactForm(data={**VALID, "message": "x" * 2001})
        self.assertFalse(form.is_valid())
        self.assertIn("message", form.errors)
