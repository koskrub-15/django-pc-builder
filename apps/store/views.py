"""The public services page."""

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


def index(
    request: HttpRequest,
) -> HttpResponse:
    """Render the services, ordering steps and FAQ page."""
    return render(
        request=request,
        template_name="store/index.html",
    )
