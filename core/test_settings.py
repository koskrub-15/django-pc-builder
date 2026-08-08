import os

os.environ.setdefault("DJANGO__SECRET_KEY", "test-only-secret-key-not-for-production")
os.environ.setdefault("DJANGO__DATABASE_URL", "sqlite://:memory:")
os.environ.setdefault("EMAIL_HOST", "localhost")
os.environ.setdefault("EMAIL_PORT", "25")
os.environ.setdefault("EMAIL_USE_TLS", "False")
os.environ.setdefault("EMAIL_HOST_USER", "test@example.com")
os.environ.setdefault("EMAIL_HOST_PASSWORD", "test")

from core.settings import *  # noqa: F403

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    },
}
