from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import (
    ListAPIView,
    ListCreateAPIView,
    RetrieveUpdateAPIView,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Invitation, Membership, Space
from .permissions import IsSpaceMember, IsSpaceOwner
from .serializers import (
    InvitationCreateSerializer,
    InvitationSerializer,
    MembershipSerializer,
    SharedSpaceCreateSerializer,
    SpaceSerializer,
)
from .services import (
    SpaceOperationError,
    cancel_invitation,
    leave_shared_space,
    remove_member,
    respond_to_invitation,
)


def _service_error(error):
    raise ValidationError({"detail": str(error)}) from error


class SpaceListCreateView(ListCreateAPIView):
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return Space.objects.filter(memberships__user=self.request.user).distinct()

    def get_serializer_class(self):
        if self.request.method == "POST":
            return SharedSpaceCreateSerializer
        return SpaceSerializer


class PersonalSpaceView(RetrieveUpdateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = SpaceSerializer
    http_method_names = ("get", "patch", "head", "options")

    def get_object(self):
        membership = get_object_or_404(
            Membership.objects.select_related("space"),
            user=self.request.user,
            space__kind=Space.Kind.PERSONAL,
            role=Membership.Role.OWNER,
        )
        self._membership = membership
        return membership.space

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if hasattr(self, "_membership"):
            context["membership"] = self._membership
        return context


class SharedSpaceDetailView(RetrieveUpdateAPIView):
    serializer_class = SpaceSerializer
    http_method_names = ("get", "patch", "head", "options")

    def get_queryset(self):
        return Space.objects.filter(kind=Space.Kind.SHARED)

    def get_permissions(self):
        permission = IsSpaceOwner if self.request.method == "PATCH" else IsSpaceMember
        return [IsAuthenticated(), permission()]


class SpaceMemberListView(ListAPIView):
    permission_classes = (IsAuthenticated, IsSpaceMember)
    serializer_class = MembershipSerializer

    def get_queryset(self):
        return Membership.objects.filter(
            space_id=self.kwargs["space_id"],
        ).select_related("user")


class SpaceMemberRemoveView(APIView):
    permission_classes = (IsAuthenticated, IsSpaceOwner)

    def delete(self, request, space_id, user_id):
        space = get_object_or_404(Space, pk=space_id, kind=Space.Kind.SHARED)
        try:
            remove_member(space, request.user, user_id)
        except SpaceOperationError as error:
            _service_error(error)
        return Response(status=status.HTTP_204_NO_CONTENT)


class LeaveSpaceView(APIView):
    permission_classes = (IsAuthenticated, IsSpaceMember)

    def post(self, request, space_id):
        space = get_object_or_404(Space, pk=space_id, kind=Space.Kind.SHARED)
        try:
            leave_shared_space(space, request.user)
        except SpaceOperationError as error:
            _service_error(error)
        return Response(status=status.HTTP_204_NO_CONTENT)


class SpaceInvitationListCreateView(ListCreateAPIView):
    permission_classes = (IsAuthenticated, IsSpaceOwner)

    def get_queryset(self):
        return Invitation.objects.filter(
            space_id=self.kwargs["space_id"],
        ).select_related("space", "invited_user", "invited_by")

    def get_serializer_class(self):
        if self.request.method == "POST":
            return InvitationCreateSerializer
        return InvitationSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["space"] = get_object_or_404(
            Space,
            pk=self.kwargs["space_id"],
            kind=Space.Kind.SHARED,
        )
        return context

    def create(self, request, *args, **kwargs):
        input_serializer = self.get_serializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        invitation = input_serializer.save()
        output_serializer = InvitationSerializer(
            invitation,
            context=self.get_serializer_context(),
        )
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


class SpaceInvitationCancelView(APIView):
    permission_classes = (IsAuthenticated, IsSpaceOwner)

    def delete(self, request, space_id, invitation_id):
        invitation = get_object_or_404(
            Invitation.objects.select_related("space"),
            pk=invitation_id,
            space_id=space_id,
        )
        try:
            cancel_invitation(invitation, request.user)
        except SpaceOperationError as error:
            _service_error(error)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ReceivedInvitationListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = InvitationSerializer

    def get_queryset(self):
        return Invitation.objects.filter(
            invited_user=self.request.user,
            status=Invitation.Status.PENDING,
        ).select_related("space", "invited_user", "invited_by")


class InvitationResponseView(APIView):
    permission_classes = (IsAuthenticated,)
    accepted = False

    def post(self, request, invitation_id):
        invitation = get_object_or_404(
            Invitation,
            pk=invitation_id,
            invited_user=request.user,
        )
        try:
            invitation = respond_to_invitation(
                invitation,
                request.user,
                accepted=self.accepted,
            )
        except SpaceOperationError as error:
            _service_error(error)
        return Response(InvitationSerializer(invitation, context={"request": request}).data)


class AcceptInvitationView(InvitationResponseView):
    accepted = True


class RejectInvitationView(InvitationResponseView):
    accepted = False
