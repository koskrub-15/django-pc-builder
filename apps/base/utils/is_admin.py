"""The staff check used by every admin-only view."""

from django.contrib.auth.models import User


def is_admin(user: User) -> bool:
    """Report whether the user may reach the staff-only views."""
    return user.is_superuser or user.is_staff
