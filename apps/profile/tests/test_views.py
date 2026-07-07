from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from apps.builder.models.pc_build import PCBuild, PCBuildOrder, PCComponent


class ProfileIndexViewTest(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username="user", password="pass")
        self.other = User.objects.create_user(username="other", password="pass")
        build = PCBuild.objects.create(name="Gaming PC")
        build.components.add(PCComponent.objects.create(name="GPU", price=Decimal("500.00")))
        self.order = PCBuildOrder.objects.create(build=build, customer=self.user)

    def test_redirects_anonymous(self) -> None:
        response = self.client.get(reverse("profile:index"))
        self.assertEqual(response.status_code, 302)

    def test_authenticated_user_sees_own_orders(self) -> None:
        self.client.login(username="user", password="pass")
        response = self.client.get(reverse("profile:index"))
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.order, response.context["orders"])

    def test_user_does_not_see_others_orders(self) -> None:
        other_build = PCBuild.objects.create(name="Other Build")
        PCBuildOrder.objects.create(build=other_build, customer=self.other)

        self.client.login(username="user", password="pass")
        response = self.client.get(reverse("profile:index"))
        orders = list(response.context["orders"])
        self.assertEqual(len(orders), 1)
        self.assertEqual(orders[0].customer, self.user)

    def test_context_includes_user(self) -> None:
        self.client.login(username="user", password="pass")
        response = self.client.get(reverse("profile:index"))
        self.assertEqual(response.context["user"], self.user)
