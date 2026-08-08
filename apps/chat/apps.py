"""Application configuration."""

from django.apps import AppConfig


class ChatConfig(AppConfig):
    """Real-time chat between customers and staff."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.chat"
