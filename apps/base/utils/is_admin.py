from django.contrib.auth.models import User


def is_admin(user: User) -> bool:
    return user.is_superuser or user.is_staff
