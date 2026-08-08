"""The homepage."""

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


def index(
    request: HttpRequest,
) -> HttpResponse:
    """Render the homepage."""
    return render(
        request=request,
        template_name="base/index.html",
    )
