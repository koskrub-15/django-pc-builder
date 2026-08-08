"""Application configuration."""

from django.apps import AppConfig


class BuilderConfig(AppConfig):
    """PC components, builds, orders and the progress tracker."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.builder"
