"""Upload path for post images."""

import uuid

from django.contrib.contenttypes.models import ContentType
from django.db import models


def build_image_path(instance: models.Model, filename: str) -> str:
    """Return a per-model upload path with a random name.

    The original filename is discarded so uploads cannot collide or be
    guessed from the URL.
    """
    content_type = ContentType.objects.get_for_model(instance)
    file_extension = filename.rsplit(".", maxsplit=1)[-1]
    return f"images/{content_type.app_label}/{content_type.model}/{uuid.uuid4()}.{file_extension}"
