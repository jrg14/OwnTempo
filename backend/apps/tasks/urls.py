from django.urls import path

from .views import TaskDetailView, TaskListCreateView

app_name = "tasks"

urlpatterns = [
    path(
        "spaces/<int:space_id>/tasks/",
        TaskListCreateView.as_view(),
        name="list",
    ),
    path(
        "spaces/<int:space_id>/tasks/<int:task_id>/",
        TaskDetailView.as_view(),
        name="detail",
    ),
]
