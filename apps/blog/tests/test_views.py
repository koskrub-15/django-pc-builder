from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from apps.blog.models.posts import Category, Comment, Post


class BlogIndexViewTest(TestCase):
    def test_empty_blog_returns_200(self) -> None:
        response = self.client.get(reverse("blog:index"))
        self.assertEqual(response.status_code, 200)

    def test_posts_appear_in_context(self) -> None:
        Post.objects.create(title="Post A", body="Body A")
        Post.objects.create(title="Post B", body="Body B")
        response = self.client.get(reverse("blog:index"))
        self.assertIn("page_obj", response.context)
        self.assertEqual(response.context["page_obj"].paginator.count, 2)

    def test_pagination_limits_to_4_per_page(self) -> None:
        for i in range(6):
            Post.objects.create(title=f"Post {i}", body="x")
        response = self.client.get(reverse("blog:index"))
        self.assertEqual(len(response.context["page_obj"]), 4)


class BlogDetailViewTest(TestCase):
    def setUp(self) -> None:
        self.post = Post.objects.create(title="Test Post", body="Body text")

    def test_get_returns_200(self) -> None:
        response = self.client.get(reverse("blog:blog_detail", args=[self.post.pk]))
        self.assertEqual(response.status_code, 200)

    def test_missing_post_returns_404(self) -> None:
        response = self.client.get(reverse("blog:blog_detail", args=[99999]))
        self.assertEqual(response.status_code, 404)

    def test_guest_can_post_comment(self) -> None:
        response = self.client.post(
            reverse("blog:blog_detail", args=[self.post.pk]),
            {"body": "Great post", "author": "Guest"},
        )
        self.assertRedirects(response, reverse("blog:blog_detail", args=[self.post.pk]))
        self.assertEqual(Comment.objects.filter(post=self.post).count(), 1)
        self.assertEqual(Comment.objects.get(post=self.post).author, "Guest")

    def test_authenticated_user_comment_uses_username(self) -> None:
        user = User.objects.create_user(username="alice", password="pass")
        self.client.login(username="alice", password="pass")
        self.client.post(
            reverse("blog:blog_detail", args=[self.post.pk]),
            {"body": "Hello"},
        )
        comment = Comment.objects.get(post=self.post)
        self.assertEqual(comment.author, "alice")

    def test_empty_body_does_not_create_comment(self) -> None:
        self.client.post(
            reverse("blog:blog_detail", args=[self.post.pk]),
            {"body": ""},
        )
        self.assertEqual(Comment.objects.filter(post=self.post).count(), 0)


class BlogCategoryViewTest(TestCase):
    def setUp(self) -> None:
        cat = Category.objects.create(name="Hardware")
        post = Post.objects.create(title="GPU Review", body="x")
        post.categories.add(cat)

    def test_category_filter_returns_matching_posts(self) -> None:
        response = self.client.get(reverse("blog:blog_category", args=["Hardware"]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["page_obj"].paginator.count, 1)

    def test_unknown_category_returns_empty(self) -> None:
        response = self.client.get(reverse("blog:blog_category", args=["NonExistent"]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["page_obj"].paginator.count, 0)


class BlogAdminViewsTest(TestCase):
    def setUp(self) -> None:
        self.staff = User.objects.create_user(username="staff", password="pass", is_staff=True)
        self.user = User.objects.create_user(username="user", password="pass")

    def test_create_post_redirects_anonymous(self) -> None:
        response = self.client.get(reverse("blog:create_post"))
        self.assertEqual(response.status_code, 302)

    def test_create_post_forbidden_for_regular_user(self) -> None:
        self.client.login(username="user", password="pass")
        response = self.client.get(reverse("blog:create_post"))
        self.assertEqual(response.status_code, 302)

    def test_create_post_accessible_for_staff(self) -> None:
        self.client.login(username="staff", password="pass")
        response = self.client.get(reverse("blog:create_post"))
        self.assertEqual(response.status_code, 200)

    def test_delete_post_removes_post(self) -> None:
        self.client.login(username="staff", password="pass")
        post = Post.objects.create(title="To Delete", body="x")
        self.client.get(reverse("blog:delete_post", args=[post.pk]))
        self.assertFalse(Post.objects.filter(pk=post.pk).exists())
