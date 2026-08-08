from decimal import Decimal

from django.contrib.auth.models import User
from django.db.utils import IntegrityError
from django.test import TestCase

from apps.builder.models.pc_build import OrderProgress, PCBuild, PCBuildOrder, PCComponent


class PCComponentTest(TestCase):
    def test_str_is_the_component_name(self) -> None:
        component = PCComponent.objects.create(name="RTX 5090", price=Decimal("1999.00"))
        self.assertEqual(str(component), "RTX 5090")

    def test_components_are_ordered_by_price_then_name(self) -> None:
        PCComponent.objects.create(name="GPU", price=Decimal("500.00"))
        PCComponent.objects.create(name="CPU", price=Decimal("300.00"))
        PCComponent.objects.create(name="AIO", price=Decimal("300.00"))
        self.assertEqual([c.name for c in PCComponent.objects.all()], ["AIO", "CPU", "GPU"])


class PCBuildTotalPriceTest(TestCase):
    def test_total_price_with_no_components(self) -> None:
        build = PCBuild.objects.create(name="Empty Build")
        self.assertEqual(build.total_price, Decimal("0.00"))

    def test_total_price_with_one_component(self) -> None:
        build = PCBuild.objects.create(name="Build")
        component = PCComponent.objects.create(name="GPU", price=Decimal("499.99"))
        build.components.add(component)
        self.assertEqual(build.total_price, Decimal("499.99"))

    def test_total_price_sums_all_components(self) -> None:
        build = PCBuild.objects.create(name="Full Build")
        build.components.add(PCComponent.objects.create(name="CPU", price=Decimal("300.00")))
        build.components.add(PCComponent.objects.create(name="GPU", price=Decimal("500.00")))
        build.components.add(PCComponent.objects.create(name="RAM", price=Decimal("100.00")))
        self.assertEqual(build.total_price, Decimal("900.00"))


class PCBuildOrderTotalPriceTest(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username="customer", password="pass")
        self.build = PCBuild.objects.create(name="Gaming Build")
        self.build.components.add(PCComponent.objects.create(name="GPU", price=Decimal("600.00")))

    def test_total_price_without_markup(self) -> None:
        order = PCBuildOrder.objects.create(build=self.build, customer=self.user)
        self.assertEqual(order.total_price, Decimal("600.00"))

    def test_total_price_with_markup(self) -> None:
        order = PCBuildOrder.objects.create(build=self.build, customer=self.user, markup=Decimal("50.00"))
        self.assertEqual(order.total_price, Decimal("650.00"))

    def test_str_includes_customer_and_build(self) -> None:
        order = PCBuildOrder.objects.create(build=self.build, customer=self.user)
        self.assertIn("customer", str(order))
        self.assertIn("Gaming Build", str(order))


class OrderProgressTest(TestCase):
    def setUp(self) -> None:
        user = User.objects.create_user(username="u", password="p")
        build = PCBuild.objects.create(name="Build")
        order = PCBuildOrder.objects.create(build=build, customer=user)
        self.progress = OrderProgress.objects.create(order=order)

    def test_str_contains_order_id(self) -> None:
        self.assertIn(str(self.progress.order.id), str(self.progress))

    def test_default_flags_are_false(self) -> None:
        self.assertFalse(self.progress.are_components_ordered)
        self.assertFalse(self.progress.is_completed)
        self.assertFalse(self.progress.is_delivered)


class MoneyConstraintTest(TestCase):
    def test_component_price_cannot_be_negative(self) -> None:
        with self.assertRaises(IntegrityError):
            PCComponent.objects.create(name="Refund", price=Decimal("-1.00"))

    def test_order_markup_cannot_be_negative(self) -> None:
        build = PCBuild.objects.create(name="Build")
        customer = User.objects.create_user(username="erin", password="pass")
        with self.assertRaises(IntegrityError):
            PCBuildOrder.objects.create(build=build, customer=customer, markup=Decimal("-5.00"))
