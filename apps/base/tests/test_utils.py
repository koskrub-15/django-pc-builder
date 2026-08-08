from django.contrib.auth.models import User
from django.test import TestCase

from apps.base.utils.is_admin import is_admin


class IsAdminTest(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username="user", password="pass")
        self.staff = User.objects.create_user(username="staff", password="pass", is_staff=True)
        self.superuser = User.objects.create_superuser(username="super", password="pass")

    def test_regular_user_is_not_admin(self) -> None:
        self.assertFalse(is_admin(self.user))

    def test_staff_user_is_admin(self) -> None:
        self.assertTrue(is_admin(self.staff))

    def test_superuser_is_admin(self) -> None:
        self.assertTrue(is_admin(self.superuser))
