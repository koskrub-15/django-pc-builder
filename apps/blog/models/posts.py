from django.db import models

from apps.blog.utils.build_image_path import build_image_path


class Category(models.Model):
    # Category pages are addressed by name, so duplicates would be unreachable.
    name = models.CharField(max_length=30, unique=True)

    class Meta:
        verbose_name_plural = "categories"
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name


class Post(models.Model):
    title = models.CharField(max_length=255)

    body = models.TextField()

    image = models.ImageField(upload_to=build_image_path, blank=True, null=True)

    created_on = models.DateTimeField(auto_now_add=True)

    last_modified = models.DateTimeField(auto_now=True)

    categories = models.ManyToManyField("Category", related_name="posts")

    def __str__(self) -> str:
        return self.title

    def __repr__(self) -> str:
        return f"<Post(id={self.pk}, title='{self.title}')>"

    class Meta:
        ordering = ("-last_modified", "-created_on", "-title")


class Comment(models.Model):
    author = models.CharField(max_length=60)
    body = models.TextField()
    created_on = models.DateTimeField(auto_now_add=True)
    post = models.ForeignKey("Post", on_delete=models.CASCADE, related_name="comments")

    def __str__(self) -> str:
        return f"{self.author} on '{self.post}'"

    class Meta:
        ordering = ("-created_on",)
