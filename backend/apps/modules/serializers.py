from rest_framework import serializers

from .catalog import get_module_definition
from .models import SpaceModule


class SpaceModuleSerializer(serializers.ModelSerializer):
    key = serializers.CharField(source="module_key", read_only=True)
    name = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    icon = serializers.SerializerMethodField()
    available = serializers.SerializerMethodField()
    route = serializers.SerializerMethodField()

    class Meta:
        model = SpaceModule
        fields = (
            "key",
            "name",
            "description",
            "icon",
            "enabled",
            "available",
            "route",
        )
        read_only_fields = (
            "key",
            "name",
            "description",
            "icon",
            "available",
            "route",
        )

    def _definition(self, configuration):
        return get_module_definition(configuration.module_key)

    def get_name(self, configuration):
        return self._definition(configuration).name

    def get_description(self, configuration):
        return self._definition(configuration).description

    def get_icon(self, configuration):
        return self._definition(configuration).icon

    def get_available(self, configuration):
        return self._definition(configuration).available

    def get_route(self, configuration):
        definition = self._definition(configuration)
        return f"/spaces/{configuration.space_id}/{definition.route_segment}/"
