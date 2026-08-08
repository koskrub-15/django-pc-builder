"""Admin registrations for the chat models."""

from django.contrib import admin

from .models import ChatMessage, ChatThread


@admin.register(ChatThread)
class ChatThreadAdmin(admin.ModelAdmin):
    """Conversations, one per customer."""

    list_display = ("id", "user")
    search_fields = ("user__username",)


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    """Individual messages, for moderation and support."""

    list_display = ("id", "thread", "sender", "timestamp")
    search_fields = ("thread__id", "sender__username", "text")
    list_filter = ("thread", "sender", "timestamp")
