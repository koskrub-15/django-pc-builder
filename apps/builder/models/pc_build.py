from decimal import Decimal

from django.contrib.auth.models import User
from django.db import models


class PCComponent(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    link = models.URLField(default="")

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name = "PC Component"
        verbose_name_plural = "PC Components"
        ordering = ("price", "name")


class PCBuild(models.Model):
    name = models.CharField(max_length=100)
    components = models.ManyToManyField(PCComponent)

    def __str__(self) -> str:
        return self.name

    @property
    def total_price(self) -> Decimal:
        return sum((component.price for component in self.components.all()), Decimal("0.00"))

    class Meta:
        verbose_name = "PC Build"
        verbose_name_plural = "PC Builds"
        ordering = ("name",)


class PCBuildOrder(models.Model):
    build = models.ForeignKey(PCBuild, on_delete=models.CASCADE)
    customer = models.ForeignKey(User, on_delete=models.CASCADE)
    created_on = models.DateTimeField(auto_now_add=True)
    address = models.CharField(max_length=100, default="The customer didn't provide an address", blank=True)
    markup = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))

    @property
    def total_price(self) -> Decimal:
        return self.build.total_price + self.markup

    def __str__(self) -> str:
        return f"{self.customer} on '{self.build}'"

    class Meta:
        verbose_name = "PC Build Order"
        verbose_name_plural = "PC Build Orders"
        ordering = ("-created_on",)


class OrderProgress(models.Model):
    order = models.OneToOneField(PCBuildOrder, on_delete=models.CASCADE, related_name="progress")
    are_components_ordered = models.BooleanField(default=False)
    are_components_arrived = models.BooleanField(default=False)
    are_components_installed = models.BooleanField(default=False)
    is_pc_build_tested = models.BooleanField(default=False)
    is_completed = models.BooleanField(default=False)
    completed_on = models.DateTimeField(blank=True, null=True)
    is_delivered = models.BooleanField(default=False)
    delivered_on = models.DateTimeField(blank=True, null=True)

    def __str__(self) -> str:
        return f"Progress for Order {self.order.id}"

    class Meta:
        verbose_name = "Order Progress"
        verbose_name_plural = "Order Progresses"
        ordering = ("-completed_on", "-order__created_on")
