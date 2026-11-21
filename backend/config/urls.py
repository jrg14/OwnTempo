"""Root URL configuration for OwnTempo."""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("apps.accounts.urls")),
    path("api/v1/", include("apps.spaces.urls")),
    path("api/v1/", include("apps.modules.urls")),
    path("api/v1/", include("apps.tasks.urls")),
    path("api/v1/", include("apps.shopping.urls")),
    path("api/v1/", include("apps.wishlist.urls")),
    path("api/v1/", include("apps.calendar.urls")),
    path("api/v1/health/", include("apps.health.urls")),
]

