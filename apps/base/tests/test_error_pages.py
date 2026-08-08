from django.template.loader import render_to_string
from django.test import TestCase


class ErrorPageTest(TestCase):
    def test_unknown_url_renders_the_custom_404(self) -> None:
        response = self.client.get("/no-such-page/")

        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, "404.html")
        self.assertContains(response, "We couldn't find that page", status_code=404)

    def test_403_page_renders(self) -> None:
        self.assertIn("403", render_to_string("403.html"))

    def test_400_page_renders(self) -> None:
        self.assertIn("400", render_to_string("400.html"))

    def test_500_page_renders_without_any_context(self) -> None:
        # The real 500 handler passes no context and no request, so this page
        # must not depend on context processors or on {% url %} resolution.
        html = render_to_string("500.html")

        self.assertIn("500", html)
        self.assertIn('href="/"', html)
