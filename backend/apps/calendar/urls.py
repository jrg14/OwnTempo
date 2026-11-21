from django.urls import path

from .views import CalendarEventDetailView, CalendarEventListCreateView

app_name = "calendar"

urlpatterns = [
    path(
        "spaces/<int:space_id>/calendar/events/",
        CalendarEventListCreateView.as_view(),
        name="event-list",
    ),
    path(
        "spaces/<int:space_id>/calendar/events/<int:event_id>/",
        CalendarEventDetailView.as_view(),
        name="event-detail",
    ),
]
