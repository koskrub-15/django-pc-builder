"""Admin registrations for the blog models."""

from django.contrib import admin

from apps.blog.models.posts import Category, Comment, Post


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Categories, managed from the site UI as well as here."""


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    """Posts, normally authored from the site UI."""


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """Reader comments, kept here for moderation."""
