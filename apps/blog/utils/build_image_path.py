import uuid

from django.contrib.contenttypes.models import ContentType
from django.db import models


def build_image_path(
    instance: models.Model,
    filename: str,
) -> str:
    """Builds a path for the image upload based on the model instance and filename."""
    # Get content type from the django model
    content_type = ContentType.objects.get_for_model(instance)

    # Get file extension
    file_extension = filename.split(".")[-1]

    # Generate new filename
    filename = f"{uuid.uuid4()}.{file_extension}"

    # Return new filename
    return f"images/{content_type.app_label}/{content_type.model}/{filename}"
