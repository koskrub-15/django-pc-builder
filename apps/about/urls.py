"""URL routes for the About page and its contact form."""

from django.urls import path

from . import views

app_name = "about"

urlpatterns = [
    path("", views.index, name="index"),
]
