from django.contrib.auth.models import User
from django.db import models


class ChatThread(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"Thread {self.id} with {self.user.username}"


class ChatMessage(models.Model):
    thread = models.ForeignKey(ChatThread, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    # Whether "text" holds markup the application composed itself (order
    # summaries, component tables). Only these are rendered unescaped — anything
    # typed by a user must stay False or it becomes a stored-XSS vector.
    is_html = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f"Message from {self.sender.username} at {self.timestamp}"
