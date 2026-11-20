from django.shortcuts import get_object_or_404
from rest_framework.generics import ListAPIView, RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated

from .models import Membership, Space
from .serializers import SpaceSerializer


class SpaceListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = SpaceSerializer

    def get_queryset(self):
        return Space.objects.filter(memberships__user=self.request.user).distinct()


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
