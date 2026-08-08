"""One conversation per customer, and the messages inside it."""

from typing import ClassVar

from django.contrib.auth.models import User
from django.db import models


class ChatThread(models.Model):
    """A customer's conversation with staff."""

    # One thread per customer: contact_admin resolves it with get_or_create,
    # which raises MultipleObjectsReturned as soon as a second one exists.
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="chat_thread")

    class Meta:
        ordering = ("-id",)

    def __str__(self) -> str:
        return f"Thread {self.id} with {self.user.username}"


class ChatMessage(models.Model):
    """A single message in a thread."""

    thread = models.ForeignKey(ChatThread, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    # Whether "text" holds markup the application composed itself (order
    # summaries, component tables). Only these are rendered unescaped — anything
    # typed by a user must stay False or it becomes a stored-XSS vector.
    is_html = models.BooleanField(default=False)

    class Meta:
        ordering = ("timestamp",)
        indexes: ClassVar[list[models.Index]] = [
            # Every read of a room is "this thread, oldest first".
            models.Index(fields=["thread", "timestamp"]),
        ]

    def __str__(self) -> str:
        return f"Message from {self.sender.username} at {self.timestamp}"
