"""Admin registrations for the build catalogue and orders."""

from typing import ClassVar

from django.contrib import admin

from apps.builder.models.pc_build import OrderProgress, PCBuild, PCBuildOrder, PCComponent


class PCComponentInline(admin.TabularInline):
    """Edits a build's components through the m2m table."""

    model = PCBuild.components.through
    extra: ClassVar[int] = 1


@admin.register(PCComponent)
class PCComponentAdmin(admin.ModelAdmin):
    """The parts catalogue."""

    list_display: ClassVar[tuple[str, ...]] = ("name", "price", "link")
    search_fields: ClassVar[tuple[str, ...]] = ("name",)
    list_filter: ClassVar[tuple[str, ...]] = ("price",)


@admin.register(PCBuild)
class PCBuildAdmin(admin.ModelAdmin):
    """Builds, with their components edited inline."""

    list_display: ClassVar[tuple[str, ...]] = ("name", "total_price")
    search_fields: ClassVar[tuple[str, ...]] = ("name",)
    inlines: ClassVar[list[admin.TabularInline]] = [PCComponentInline]
    exclude: ClassVar[tuple[str, ...]] = ("components",)


@admin.register(OrderProgress)
class OrderProgressAdmin(admin.ModelAdmin):
    """Assembly milestones; staff normally use the tracker page instead."""

    list_display: ClassVar[tuple[str, ...]] = (
        "order",
        "are_components_ordered",
        "are_components_arrived",
        "are_components_installed",
        "is_pc_build_tested",
        "is_completed",
        "completed_on",
        "is_delivered",
        "delivered_on",
    )
    list_filter: ClassVar[tuple[str, ...]] = (
        "are_components_ordered",
        "are_components_arrived",
        "are_components_installed",
        "is_pc_build_tested",
        "is_completed",
        "is_delivered",
    )
    search_fields: ClassVar[tuple[str, ...]] = ("order__customer__username", "order__build__name")


class OrderProgressInline(admin.StackedInline):
    """Shows an order's progress row on the order page."""

    model = OrderProgress
    can_delete: ClassVar[bool] = False
    verbose_name_plural: ClassVar[str] = "Order Progress"


@admin.register(PCBuildOrder)
class PCBuildOrderAdmin(admin.ModelAdmin):
    """Customer orders, with their progress inline."""

    list_display: ClassVar[tuple[str, ...]] = ("build", "customer", "created_on")
    list_filter: ClassVar[tuple[str, ...]] = ("created_on",)
    search_fields: ClassVar[tuple[str, ...]] = ("customer__username", "build__name")
    inlines: ClassVar[list[admin.StackedInline]] = [OrderProgressInline]
