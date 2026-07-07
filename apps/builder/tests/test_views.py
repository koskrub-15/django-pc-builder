from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from apps.builder.models.pc_build import PCBuild, PCBuildOrder, PCComponent, OrderProgress


class BuilderAccessTest(TestCase):
    """All builder views require staff access."""

    def setUp(self) -> None:
        self.staff = User.objects.create_user(username="staff", password="pass", is_staff=True)
        self.user = User.objects.create_user(username="user", password="pass")

    def test_builds_redirects_anonymous(self) -> None:
        response = self.client.get(reverse("builder:builds"))
        self.assertEqual(response.status_code, 302)

    def test_builds_forbidden_for_regular_user(self) -> None:
        self.client.login(username="user", password="pass")
        response = self.client.get(reverse("builder:builds"))
        self.assertEqual(response.status_code, 302)

    def test_builds_accessible_for_staff(self) -> None:
        self.client.login(username="staff", password="pass")
        response = self.client.get(reverse("builder:builds"))
        self.assertEqual(response.status_code, 200)

    def test_tracker_accessible_for_staff(self) -> None:
        self.client.login(username="staff", password="pass")
        response = self.client.get(reverse("builder:tracker"))
        self.assertEqual(response.status_code, 200)

    def test_create_component_accessible_for_staff(self) -> None:
        self.client.login(username="staff", password="pass")
        response = self.client.get(reverse("builder:create_component"))
        self.assertEqual(response.status_code, 200)


class CreateComponentViewTest(TestCase):
    def setUp(self) -> None:
        self.staff = User.objects.create_user(username="staff", password="pass", is_staff=True)
        self.client.login(username="staff", password="pass")

    def test_post_valid_data_creates_component(self) -> None:
        self.client.post(
            reverse("builder:create_component"),
            {"name": "RTX 4090", "price": "1599.99", "link": "https://nvidia.com"},
        )
        self.assertTrue(PCComponent.objects.filter(name="RTX 4090").exists())

    def test_post_invalid_data_does_not_create(self) -> None:
        self.client.post(
            reverse("builder:create_component"),
            {"name": "", "price": "bad", "link": ""},
        )
        self.assertEqual(PCComponent.objects.count(), 0)


class ListPCBuildsViewTest(TestCase):
    def setUp(self) -> None:
        self.staff = User.objects.create_user(username="staff", password="pass", is_staff=True)
        self.client.login(username="staff", password="pass")

    def test_get_shows_existing_builds(self) -> None:
        PCBuild.objects.create(name="Budget Build")
        response = self.client.get(reverse("builder:builds"))
        self.assertContains(response, "Budget Build")

    def test_post_creates_build(self) -> None:
        self.client.post(reverse("builder:builds"), {"name": "New Build"})
        self.assertTrue(PCBuild.objects.filter(name="New Build").exists())

    def test_post_with_components_sets_m2m(self) -> None:
        component = PCComponent.objects.create(name="CPU", price=Decimal("200.00"))
        self.client.post(
            reverse("builder:builds"),
            {"name": "Build With CPU", "components": [str(component.pk)]},
        )
        build = PCBuild.objects.get(name="Build With CPU")
        self.assertIn(component, build.components.all())


class ProgressTrackerViewTest(TestCase):
    def setUp(self) -> None:
        self.staff = User.objects.create_user(username="staff", password="pass", is_staff=True)
        self.customer = User.objects.create_user(username="customer", password="pass", email="c@example.com")
        self.client.login(username="staff", password="pass")

        build = PCBuild.objects.create(name="Build")
        self.order = PCBuildOrder.objects.create(build=build, customer=self.customer)
        self.progress = OrderProgress.objects.create(order=self.order)

    def test_get_returns_200(self) -> None:
        response = self.client.get(reverse("builder:tracker"))
        self.assertEqual(response.status_code, 200)

    def test_post_updates_progress_flags(self) -> None:
        self.client.post(
            reverse("builder:tracker"),
            {f"ordered_{self.order.id}": "on", f"arrived_{self.order.id}": "on"},
        )
        self.progress.refresh_from_db()
        self.assertTrue(self.progress.are_components_ordered)
        self.assertTrue(self.progress.are_components_arrived)
        self.assertFalse(self.progress.are_components_installed)
