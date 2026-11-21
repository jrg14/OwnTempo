from django.urls import path

from .views import (
    ShoppingItemCreateView,
    ShoppingItemDetailView,
    ShoppingItemReorderView,
    ShoppingListDetailView,
    ShoppingListListCreateView,
)

app_name = "shopping"

urlpatterns = [
    path(
        "spaces/<int:space_id>/shopping/lists/",
        ShoppingListListCreateView.as_view(),
        name="list",
    ),
    path(
        "spaces/<int:space_id>/shopping/lists/<int:list_id>/",
        ShoppingListDetailView.as_view(),
        name="detail",
    ),
    path(
        "spaces/<int:space_id>/shopping/lists/<int:list_id>/items/",
        ShoppingItemCreateView.as_view(),
        name="item-create",
    ),
    path(
        "spaces/<int:space_id>/shopping/lists/<int:list_id>/items/reorder/",
        ShoppingItemReorderView.as_view(),
        name="item-reorder",
    ),
    path(
        "spaces/<int:space_id>/shopping/lists/<int:list_id>/items/<int:item_id>/",
        ShoppingItemDetailView.as_view(),
        name="item-detail",
    ),
]
