from django.urls import path

from . import views

app_name = "builder"

urlpatterns = [
    path("builds/", views.list_of_pc_builds, name="builds"),
    path("tracker/", views.progress_tracker, name="tracker"),
    path("builds/create_component/", views.create_component, name="create_component"),
    path("builds/edit_component/<int:pk>/", views.edit_component, name="edit_component"),
    path("builds/<int:pk>/", views.update_build, name="update_build"),
]
