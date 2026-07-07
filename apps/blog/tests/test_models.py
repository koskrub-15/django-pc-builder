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
        Post.objects.create(title="Older", body="x")
        posts = list(Post.objects.all())
        self.assertEqual(posts[0], self.post)


class CommentModelTest(TestCase):
    def setUp(self) -> None:
        post = Post.objects.create(title="Post", body="Body")
        self.comment = Comment.objects.create(author="Alice", body="Nice post", post=post)

    def test_str(self) -> None:
        self.assertEqual(str(self.comment), "Alice on 'Post'")
