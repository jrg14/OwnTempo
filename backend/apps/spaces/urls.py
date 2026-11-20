from django.urls import path

from .views import PersonalSpaceView, SpaceListView

app_name = "spaces"

urlpatterns = [
    path("spaces/", SpaceListView.as_view(), name="list"),
    path("spaces/personal/", PersonalSpaceView.as_view(), name="personal"),
]
