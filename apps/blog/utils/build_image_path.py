import uuid

from django.contrib.contenttypes.models import ContentType
from django.db import models


def build_image_path(instance: models.Model, filename: str) -> str:
    content_type = ContentType.objects.get_for_model(instance)
    file_extension = filename.split(".")[-1]
    return f"images/{content_type.app_label}/{content_type.model}/{uuid.uuid4()}.{file_extension}"
