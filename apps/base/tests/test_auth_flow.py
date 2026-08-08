from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class LogoutTest(TestCase):
    """Logging out must require a POST, or any page can log the user out."""

    def setUp(self) -> None:
        User.objects.create_user(username="user", password="pass")
        self.client.login(username="user", password="pass")

    def test_get_shows_a_confirmation_page_without_logging_out(self) -> None:
        response = self.client.get(reverse("account_logout"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("_auth_user_id", self.client.session)

    def test_confirmation_page_renders_all_its_urls(self) -> None:
        # The page used to reference a url name that does not exist; it never
        # showed because logout happened on GET, so nothing caught it.
        response = self.client.get(reverse("account_logout"))
        self.assertContains(response, reverse("base:index"))

    def test_post_logs_the_user_out(self) -> None:
        self.client.post(reverse("account_logout"))
        self.assertNotIn("_auth_user_id", self.client.session)
