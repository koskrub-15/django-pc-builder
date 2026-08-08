"""Application configuration."""

from django.apps import AppConfig


class BlogConfig(AppConfig):
    """Posts, categories and comments."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.blog"
