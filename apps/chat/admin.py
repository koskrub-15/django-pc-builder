from django.contrib import admin

from .models import ChatMessage, ChatThread


@admin.register(ChatThread)
class ChatThreadAdmin(admin.ModelAdmin):
    list_display = ("id", "user")
    search_fields = ("user__username",)


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "thread", "sender", "timestamp")
    search_fields = ("thread__id", "sender__username", "text")
    list_filter = ("thread", "sender", "timestamp")
