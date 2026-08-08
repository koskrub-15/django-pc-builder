from django.test import TestCase
from django.urls import reverse


class BaseIndexViewTest(TestCase):
    def test_returns_200(self) -> None:
        response = self.client.get(reverse("base:index"))
        self.assertEqual(response.status_code, 200)

    def test_uses_base_template(self) -> None:
        response = self.client.get(reverse("base:index"))
        self.assertTemplateUsed(response, "base/index.html")
