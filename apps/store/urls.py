"""URL routes for the services page."""

from django.urls import path

from . import views

app_name = "store"

urlpatterns = [
    path("", views.index, name="index"),
]
