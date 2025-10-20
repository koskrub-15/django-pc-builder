from django.urls import path

from apps.blog import views

app_name = "blog"

urlpatterns = [
    path("", views.index, name="index"),
    path("post/<int:pk>/", views.blog_detail, name="blog_detail"),
    path("category/<category>/", views.blog_category, name="blog_category"),
    path("create/", views.create_post, name="create_post"),
    path("delete/<int:pk>/", views.delete_post, name="delete_post"),
    path("update/<int:pk>/", views.update_post, name="update_post"),
    path("categories/", views.create_category, name="categories"),
    path("categories/update/<int:pk>/", views.update_category, name="update_category"),
    path("categories/delete/<int:pk>/", views.delete_category, name="delete_category"),
]
