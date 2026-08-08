"""Forms for commenting on posts and for authoring them."""

from typing import ClassVar

from django import forms

from apps.blog.models.posts import Category, Post


class CommentForm(forms.Form):
    """A reply to a post; the author field is only used for guests."""

    author = forms.CharField(
        max_length=60,
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Your Name (for guests)"},
        ),
    )
    body = forms.CharField(
        widget=forms.Textarea(
            attrs={"class": "form-control", "placeholder": "Leave a comment!"},
        ),
    )


class PostForm(forms.ModelForm):
    """Create or edit a post, including its image and categories."""

    class Meta:
        model = Post
        fields: ClassVar[list[str]] = ["title", "body", "categories", "image"]
        widgets: ClassVar[dict] = {
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Title"}),
            "body": forms.Textarea(attrs={"class": "form-control", "placeholder": "Write your post here..."}),
            "categories": forms.SelectMultiple(
                attrs={
                    "class": "form-select",
                    "data-placeholder": "Select categories...",
                },
            ),
        }


class CategoryForm(forms.ModelForm):
    """Create or rename a category."""

    class Meta:
        model = Category
        fields: ClassVar[list[str]] = ["name"]
        widgets: ClassVar[dict] = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter category name",
                },
            ),
        }
