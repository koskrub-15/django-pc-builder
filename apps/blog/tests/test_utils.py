import re

from django.test import TestCase

from apps.blog.models.posts import Post
from apps.blog.utils.build_image_path import build_image_path

UUID_HEX_PATTERN = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"


class BuildImagePathTest(TestCase):
    def setUp(self) -> None:
        self.post = Post.objects.create(title="Post", body="Body")

    def test_path_is_namespaced_by_app_and_model(self) -> None:
        path = build_image_path(self.post, "photo.png")
        self.assertTrue(path.startswith("images/blog/post/"))

    def test_extension_is_preserved(self) -> None:
        path = build_image_path(self.post, "photo.png")
        self.assertTrue(path.endswith(".png"))

    def test_filename_is_a_uuid(self) -> None:
        path = build_image_path(self.post, "photo.png")
        filename = path.rsplit("/", maxsplit=1)[-1]
        self.assertRegex(filename, rf"^{UUID_HEX_PATTERN}\.png$")

    def test_names_are_unique_for_the_same_upload(self) -> None:
        first = build_image_path(self.post, "photo.png")
        second = build_image_path(self.post, "photo.png")
        self.assertNotEqual(first, second)

    def test_only_the_last_dot_starts_the_extension(self) -> None:
        path = build_image_path(self.post, "my.holiday.photo.jpeg")
        self.assertTrue(path.endswith(".jpeg"))
        self.assertEqual(len(re.findall(r"\.", path.rsplit("/", maxsplit=1)[-1])), 1)
