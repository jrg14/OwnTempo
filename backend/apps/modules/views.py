from rest_framework.generics import ListAPIView, UpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.spaces.permissions import IsSpaceMember, IsSpaceOwner

from .catalog import MODULE_CATALOG
from .models import SpaceModule
from .serializers import SpaceModuleSerializer


class ModuleCatalogView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        return Response(
            [
                {
                    "key": module.key,
                    "name": module.name,
                    "description": module.description,
                    "icon": module.icon,
                    "app_label": module.app_label,
                    "available": module.available,
                }
                for module in MODULE_CATALOG
            ]
        )


class SpaceModuleListView(ListAPIView):
    permission_classes = (IsAuthenticated, IsSpaceMember)
    serializer_class = SpaceModuleSerializer

    def get_queryset(self):
        return SpaceModule.objects.filter(space_id=self.kwargs["space_id"])


class SpaceModuleUpdateView(UpdateAPIView):
    permission_classes = (IsAuthenticated, IsSpaceOwner)
    serializer_class = SpaceModuleSerializer
    lookup_field = "module_key"
    lookup_url_kwarg = "module_key"
    http_method_names = ("patch", "options")

    def get_queryset(self):
        return SpaceModule.objects.filter(space_id=self.kwargs["space_id"])
