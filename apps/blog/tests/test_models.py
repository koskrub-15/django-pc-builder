from django.db.utils import IntegrityError
from django.test import TestCase

from apps.blog.models.posts import Category, Comment, Post


class CategoryModelTest(TestCase):
    def test_str(self) -> None:
        cat = Category.objects.create(name="Tech")
        self.assertEqual(str(cat), "Tech")


class PostModelTest(TestCase):
    def setUp(self) -> None:
        self.category = Category.objects.create(name="Tech")
        self.post = Post.objects.create(title="Test Post", body="Body text")
        self.post.categories.add(self.category)

    def test_str(self) -> None:
        self.assertEqual(str(self.post), "Test Post")

    def test_repr(self) -> None:
        self.assertIn(f"id={self.post.pk}", repr(self.post))
        self.assertIn("Test Post", repr(self.post))

    def test_default_ordering_is_by_last_modified_desc(self) -> None:
        newer = Post.objects.create(title="Newer", body="x")
        posts = list(Post.objects.all())
        self.assertEqual(posts[0], newer)


class CommentModelTest(TestCase):
    def setUp(self) -> None:
        post = Post.objects.create(title="Post", body="Body")
        self.comment = Comment.objects.create(author="Alice", body="Nice post", post=post)

    def test_str(self) -> None:
        self.assertEqual(str(self.comment), "Alice on 'Post'")

    def test_post_exposes_its_comments(self) -> None:
        self.assertEqual(list(self.comment.post.comments.all()), [self.comment])


class CategoryConstraintTest(TestCase):
    def test_category_names_are_unique(self) -> None:
        Category.objects.create(name="Hardware")
        with self.assertRaises(IntegrityError):
            Category.objects.create(name="Hardware")
