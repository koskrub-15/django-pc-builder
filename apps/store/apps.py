"""Application configuration."""

from django.apps import AppConfig


class StoreConfig(AppConfig):
    """Public services, ordering steps and FAQ page."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.store"
