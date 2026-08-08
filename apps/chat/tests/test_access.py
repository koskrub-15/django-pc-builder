from django.contrib.auth.models import AnonymousUser, User
from django.http import Http404
from django.test import TestCase

from apps.chat.models import ChatThread
from apps.chat.utils.access import get_accessible_thread, may_access_thread


class MayAccessThreadTest(TestCase):
    def setUp(self) -> None:
        self.owner = User.objects.create_user(username="owner", password="pass")
        self.thread = ChatThread.objects.create(user=self.owner)

    def test_owner_may_access(self) -> None:
        self.assertTrue(may_access_thread(self.owner, self.thread))

    def test_staff_may_access_any_thread(self) -> None:
        staff = User.objects.create_user(username="staff", password="pass", is_staff=True)
        self.assertTrue(may_access_thread(staff, self.thread))

    def test_other_user_may_not_access(self) -> None:
        intruder = User.objects.create_user(username="mallory", password="pass")
        self.assertFalse(may_access_thread(intruder, self.thread))

    def test_anonymous_may_not_access(self) -> None:
        # The views are all @login_required and the consumer rejects anonymous
        # sockets before asking, so this is the belt to those braces.
        self.assertFalse(may_access_thread(AnonymousUser(), self.thread))

    def test_get_accessible_thread_returns_the_thread_for_its_owner(self) -> None:
        self.assertEqual(get_accessible_thread(self.owner, self.thread.id), self.thread)

    def test_get_accessible_thread_hides_someone_elses_thread(self) -> None:
        intruder = User.objects.create_user(username="mallory", password="pass")
        with self.assertRaises(Http404):
            get_accessible_thread(intruder, self.thread.id)

    def test_get_accessible_thread_raises_for_a_missing_thread(self) -> None:
        with self.assertRaises(Http404):
            get_accessible_thread(self.owner, 99999)
