"""Application configuration."""

from django.apps import AppConfig


class ProfileConfig(AppConfig):
    """Order history for the signed-in customer."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.profile"
