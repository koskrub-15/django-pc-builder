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
        User.objects.create_user(username="alice", password="pass")
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

    def test_post_without_body_field_renders_blank_form(self) -> None:
        response = self.client.post(
            reverse("blog:blog_detail", args=[self.post.pk]),
            {"author": "Guest"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["form"].is_bound)
        self.assertEqual(Comment.objects.filter(post=self.post).count(), 0)

    def test_guest_without_name_is_anonymous(self) -> None:
        self.client.post(
            reverse("blog:blog_detail", args=[self.post.pk]),
            {"body": "No name given", "author": ""},
        )
        self.assertEqual(Comment.objects.get(post=self.post).author, "Anonymous")


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


class CreatePostViewTest(TestCase):
    def setUp(self) -> None:
        User.objects.create_user(username="staff", password="pass", is_staff=True)
        self.client.login(username="staff", password="pass")
        self.category = Category.objects.create(name="Hardware")

    def test_post_valid_data_creates_post(self) -> None:
        response = self.client.post(
            reverse("blog:create_post"),
            {"title": "Brand New", "body": "Body text", "categories": [str(self.category.pk)]},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Post.objects.filter(title="Brand New").exists())

    def test_post_invalid_data_redisplays_form(self) -> None:
        response = self.client.post(reverse("blog:create_post"), {"title": "", "body": ""})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Post.objects.count(), 0)
        self.assertTrue(response.context["form"].errors)


class UpdatePostViewTest(TestCase):
    def setUp(self) -> None:
        User.objects.create_user(username="staff", password="pass", is_staff=True)
        self.client.login(username="staff", password="pass")
        self.post = Post.objects.create(title="Original", body="Original body")
        self.category = Category.objects.create(name="Hardware")
        self.post.categories.add(self.category)

    def test_get_prefills_form_with_post(self) -> None:
        response = self.client.get(reverse("blog:update_post", args=[self.post.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["post"], self.post)
        self.assertEqual(response.context["form"].initial["title"], "Original")

    def test_post_valid_data_updates_post(self) -> None:
        response = self.client.post(
            reverse("blog:update_post", args=[self.post.pk]),
            {"title": "Renamed", "body": "New body", "categories": [str(self.category.pk)]},
        )
        self.assertEqual(response.status_code, 302)
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, "Renamed")

    def test_post_invalid_data_leaves_post_unchanged(self) -> None:
        response = self.client.post(
            reverse("blog:update_post", args=[self.post.pk]),
            {"title": "", "body": ""},
        )
        self.assertEqual(response.status_code, 200)
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, "Original")


class CategoryAdminViewsTest(TestCase):
    def setUp(self) -> None:
        User.objects.create_user(username="staff", password="pass", is_staff=True)
        self.client.login(username="staff", password="pass")

    def test_get_categories_page_lists_categories(self) -> None:
        Category.objects.create(name="Hardware")
        response = self.client.get(reverse("blog:categories"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["categories"]), 1)

    def test_post_creates_category(self) -> None:
        response = self.client.post(reverse("blog:categories"), {"name": "Cooling"})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Category.objects.filter(name="Cooling").exists())

    def test_post_invalid_category_is_rejected(self) -> None:
        response = self.client.post(reverse("blog:categories"), {"name": ""})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Category.objects.count(), 0)

    def test_get_update_category_prefills_form(self) -> None:
        category = Category.objects.create(name="Old Name")
        response = self.client.get(reverse("blog:update_category", args=[category.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["category"], category)

    def test_post_update_category_renames_it(self) -> None:
        category = Category.objects.create(name="Old Name")
        response = self.client.post(
            reverse("blog:update_category", args=[category.pk]),
            {"name": "New Name"},
        )
        self.assertRedirects(response, "/blog/categories/")
        category.refresh_from_db()
        self.assertEqual(category.name, "New Name")

    def test_post_update_category_invalid_keeps_name(self) -> None:
        category = Category.objects.create(name="Old Name")
        response = self.client.post(reverse("blog:update_category", args=[category.pk]), {"name": ""})
        self.assertEqual(response.status_code, 200)
        category.refresh_from_db()
        self.assertEqual(category.name, "Old Name")

    def test_update_missing_category_returns_404(self) -> None:
        response = self.client.get(reverse("blog:update_category", args=[99999]))
        self.assertEqual(response.status_code, 404)

    def test_delete_category_removes_it(self) -> None:
        category = Category.objects.create(name="Doomed")
        response = self.client.get(reverse("blog:delete_category", args=[category.pk]))
        self.assertRedirects(response, "/blog/categories/")
        self.assertFalse(Category.objects.filter(pk=category.pk).exists())

    def test_delete_missing_category_returns_404(self) -> None:
        response = self.client.get(reverse("blog:delete_category", args=[99999]))
        self.assertEqual(response.status_code, 404)
