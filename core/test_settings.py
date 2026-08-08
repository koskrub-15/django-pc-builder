"""Test settings: in-memory SQLite, in-memory channel layer, locmem email.

No .env and no services are needed; CI runs with nothing but a checkout.
"""

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

# core.settings turns the production hardening on whenever DEBUG is false, and
# DEBUG comes from the environment. Without this the whole suite depends on
# whether a .env happens to exist: with one it passes, and on a bare checkout
# SECURE_SSL_REDIRECT answers every test request with a 301.
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_HSTS_SECONDS = 0

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    },
}
