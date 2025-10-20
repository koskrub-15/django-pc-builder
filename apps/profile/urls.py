from django.urls import path

from apps.profile import views

app_name = "profile"


urlpatterns = [
    path("", views.index, name="index"),
]
