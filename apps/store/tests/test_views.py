from django.test import TestCase
from django.urls import reverse


class StoreIndexViewTest(TestCase):
    def test_returns_200(self) -> None:
        response = self.client.get(reverse("store:index"))
        self.assertEqual(response.status_code, 200)

    def test_uses_store_template(self) -> None:
        response = self.client.get(reverse("store:index"))
        self.assertTemplateUsed(response, "store/index.html")
