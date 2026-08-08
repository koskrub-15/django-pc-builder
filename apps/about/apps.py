"""Application configuration."""

from django.apps import AppConfig


class AboutConfig(AppConfig):
    """About page and contact form."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.about"
