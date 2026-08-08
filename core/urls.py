"""Root URL configuration."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.base.urls")),
    path("about/", include("apps.about.urls")),
    path("blog/", include("apps.blog.urls")),
    path("store/", include("apps.store.urls")),
    path("chat/", include("apps.chat.urls")),
    path("builder/", include("apps.builder.urls")),
    path("accounts/", include("allauth.urls")),
    path("profile/", include("apps.profile.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
