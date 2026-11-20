from django.urls import path

from .views import (
    AcceptInvitationView,
    LeaveSpaceView,
    PersonalSpaceView,
    ReceivedInvitationListView,
    RejectInvitationView,
    SharedSpaceDetailView,
    SpaceInvitationCancelView,
    SpaceInvitationListCreateView,
    SpaceListCreateView,
    SpaceMemberListView,
    SpaceMemberRemoveView,
)

app_name = "spaces"

urlpatterns = [
    path("spaces/", SpaceListCreateView.as_view(), name="list"),
    path("spaces/personal/", PersonalSpaceView.as_view(), name="personal"),
    path("spaces/<int:pk>/", SharedSpaceDetailView.as_view(), name="detail"),
    path(
        "spaces/<int:space_id>/members/",
        SpaceMemberListView.as_view(),
        name="member-list",
    ),
    path(
        "spaces/<int:space_id>/members/<int:user_id>/",
        SpaceMemberRemoveView.as_view(),
        name="member-remove",
    ),
    path(
        "spaces/<int:space_id>/leave/",
        LeaveSpaceView.as_view(),
        name="leave",
    ),
    path(
        "spaces/<int:space_id>/invitations/",
        SpaceInvitationListCreateView.as_view(),
        name="invitation-list",
    ),
    path(
        "spaces/<int:space_id>/invitations/<int:invitation_id>/",
        SpaceInvitationCancelView.as_view(),
        name="invitation-cancel",
    ),
    path(
        "invitations/",
        ReceivedInvitationListView.as_view(),
        name="received-invitations",
    ),
    path(
        "invitations/<int:invitation_id>/accept/",
        AcceptInvitationView.as_view(),
        name="invitation-accept",
    ),
    path(
        "invitations/<int:invitation_id>/reject/",
        RejectInvitationView.as_view(),
        name="invitation-reject",
    ),
]
