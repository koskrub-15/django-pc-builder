"""URL routes for the homepage."""

from django.urls import path

from . import views

app_name = "base"

urlpatterns = [
    # base:index
    path("", views.index, name="index"),
]
