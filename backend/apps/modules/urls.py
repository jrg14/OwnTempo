from django.urls import path

from .views import ModuleCatalogView, SpaceModuleListView, SpaceModuleUpdateView

app_name = "modules"

urlpatterns = [
    path("modules/catalog/", ModuleCatalogView.as_view(), name="catalog"),
    path(
        "spaces/<int:space_id>/modules/",
        SpaceModuleListView.as_view(),
        name="space-module-list",
    ),
    path(
        "spaces/<int:space_id>/modules/<str:module_key>/",
        SpaceModuleUpdateView.as_view(),
        name="space-module-update",
    ),
]
