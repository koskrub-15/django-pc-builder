from decimal import Decimal
from unittest.mock import Mock, patch

from django.contrib.auth.models import User
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from apps.builder.models.pc_build import (
    OrderProgress,
    PCBuild,
    PCBuildOrder,
    PCComponent,
)


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

    @patch("apps.builder.views.notify_user_about_order")
    def test_marking_completed_stamps_date_and_notifies(self, mock_notify: Mock) -> None:
        self.client.post(reverse("builder:tracker"), {f"completed_{self.order.id}": "on"})
        self.progress.refresh_from_db()
        self.assertTrue(self.progress.is_completed)
        self.assertIsNotNone(self.progress.completed_on)
        mock_notify.assert_called_once()
        self.assertFalse(mock_notify.call_args.kwargs["is_delivered"])

    @patch("apps.builder.views.notify_user_about_order")
    def test_marking_delivered_stamps_date_and_notifies(self, mock_notify: Mock) -> None:
        self.client.post(reverse("builder:tracker"), {f"delivered_{self.order.id}": "on"})
        self.progress.refresh_from_db()
        self.assertTrue(self.progress.is_delivered)
        self.assertIsNotNone(self.progress.delivered_on)
        self.assertTrue(mock_notify.call_args.kwargs["is_delivered"])

    @patch("apps.builder.views.notify_user_about_order")
    def test_already_completed_order_is_not_notified_again(self, mock_notify: Mock) -> None:
        self.progress.is_completed = True
        self.progress.save()
        self.client.post(reverse("builder:tracker"), {f"completed_{self.order.id}": "on"})
        mock_notify.assert_not_called()

    @patch("apps.builder.views.notify_user_about_order")
    def test_unchecking_completed_clears_the_date(self, mock_notify: Mock) -> None:
        self.progress.is_completed = True
        self.progress.completed_on = timezone.now()
        self.progress.save()
        self.client.post(reverse("builder:tracker"), {})
        self.progress.refresh_from_db()
        self.assertFalse(self.progress.is_completed)
        self.assertIsNone(self.progress.completed_on)
        mock_notify.assert_not_called()

    def test_post_redirects_back_to_tracker(self) -> None:
        response = self.client.post(reverse("builder:tracker"), {})
        self.assertRedirects(response, reverse("builder:tracker"))


class UpdateBuildViewTest(TestCase):
    def setUp(self) -> None:
        User.objects.create_user(username="staff", password="pass", is_staff=True)
        self.client.login(username="staff", password="pass")
        self.build = PCBuild.objects.create(name="Original Build")
        self.component = PCComponent.objects.create(name="GPU", price=Decimal("500.00"))

    def test_get_prefills_form_with_build(self) -> None:
        response = self.client.get(reverse("builder:update_build", args=[self.build.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["build"], self.build)

    def test_post_renames_build(self) -> None:
        response = self.client.post(
            reverse("builder:update_build", args=[self.build.pk]),
            {"name": "Renamed Build"},
        )
        self.assertRedirects(response, reverse("builder:builds"))
        self.build.refresh_from_db()
        self.assertEqual(self.build.name, "Renamed Build")

    def test_post_replaces_components(self) -> None:
        self.client.post(
            reverse("builder:update_build", args=[self.build.pk]),
            {"name": "Original Build", "components": [str(self.component.pk)]},
        )
        self.assertIn(self.component, self.build.components.all())

    def test_post_invalid_data_keeps_name(self) -> None:
        response = self.client.post(reverse("builder:update_build", args=[self.build.pk]), {"name": ""})
        self.assertEqual(response.status_code, 200)
        self.build.refresh_from_db()
        self.assertEqual(self.build.name, "Original Build")


class EditComponentViewTest(TestCase):
    def setUp(self) -> None:
        User.objects.create_user(username="staff", password="pass", is_staff=True)
        self.client.login(username="staff", password="pass")
        self.component = PCComponent.objects.create(name="Old CPU", price=Decimal("100.00"))

    def test_get_prefills_form_with_component(self) -> None:
        response = self.client.get(reverse("builder:edit_component", args=[self.component.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["component"], self.component)

    def test_post_updates_component(self) -> None:
        response = self.client.post(
            reverse("builder:edit_component", args=[self.component.pk]),
            {"name": "New CPU", "price": "250.50", "link": "https://example.com"},
        )
        self.assertRedirects(response, reverse("builder:builds"))
        self.component.refresh_from_db()
        self.assertEqual(self.component.name, "New CPU")
        self.assertEqual(self.component.price, Decimal("250.50"))

    def test_post_invalid_data_keeps_component(self) -> None:
        response = self.client.post(
            reverse("builder:edit_component", args=[self.component.pk]),
            {"name": "", "price": "not-a-number", "link": ""},
        )
        self.assertEqual(response.status_code, 200)
        self.component.refresh_from_db()
        self.assertEqual(self.component.name, "Old CPU")


class TrackerQueryCountTest(TestCase):
    """The tracker renders build, customer and components per order."""

    def setUp(self) -> None:
        User.objects.create_user(username="staff", password="pass", is_staff=True)
        self.client.login(username="staff", password="pass")

    def _add_order(self, name: str) -> None:
        build = PCBuild.objects.create(name=name)
        build.components.add(PCComponent.objects.create(name=f"part-{name}", price=Decimal("10.00")))
        customer = User.objects.create_user(username=f"customer-{name}", password="pass")
        order = PCBuildOrder.objects.create(build=build, customer=customer)
        OrderProgress.objects.create(order=order)

    def _queries_for_tracker(self) -> int:
        with CaptureQueriesContext(connection) as ctx:
            self.client.get(reverse("builder:tracker"))
        return len(ctx.captured_queries)

    def test_query_count_does_not_grow_with_the_number_of_orders(self) -> None:
        self._add_order("one")
        baseline = self._queries_for_tracker()

        for name in ("two", "three", "four"):
            self._add_order(name)

        self.assertEqual(self._queries_for_tracker(), baseline)
