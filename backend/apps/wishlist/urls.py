from django.urls import path

from .views import WishDetailView, WishListCreateView

app_name = "wishlist"

urlpatterns = [
    path(
        "spaces/<int:space_id>/wishlist/",
        WishListCreateView.as_view(),
        name="list",
    ),
    path(
        "spaces/<int:space_id>/wishlist/<int:wish_id>/",
        WishDetailView.as_view(),
        name="detail",
    ),
]
