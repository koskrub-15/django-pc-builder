"""Access rules shared by the chat HTTP views and the WebSocket consumer."""

from django.contrib.auth.models import AbstractBaseUser, AnonymousUser
from django.http import Http404
from django.shortcuts import get_object_or_404

from apps.chat.models import ChatThread


def may_access_thread(user: AbstractBaseUser | AnonymousUser, thread: ChatThread) -> bool:
    """Report whether the user is allowed to read and post in the thread."""
    if not user.is_authenticated:
        return False
    return bool(user.is_staff) or thread.user_id == user.pk


def get_accessible_thread(user: AbstractBaseUser | AnonymousUser, thread_id: int) -> ChatThread:
    """Return the thread the user may access, or raise Http404.

    A thread the user may not access is reported as missing rather than
    forbidden, so thread ids cannot be enumerated from the response code.
    """
    thread = get_object_or_404(ChatThread, id=thread_id)
    if not may_access_thread(user, thread):
        raise Http404
    return thread
