from django.contrib import admin

from .models import SpaceModule


@admin.register(SpaceModule)
class SpaceModuleAdmin(admin.ModelAdmin):
    list_display = ("space", "module_key", "enabled", "updated_at")
    list_filter = ("module_key", "enabled")
    search_fields = ("space__name",)
    readonly_fields = ("created_at", "updated_at")
