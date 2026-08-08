"""Application configuration."""

from django.apps import AppConfig


class BaseConfig(AppConfig):
    """Homepage and helpers shared across the other apps."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.base"
