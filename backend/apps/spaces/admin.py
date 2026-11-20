from django.contrib import admin

from .models import Invitation, Membership, Space


class MembershipInline(admin.TabularInline):
    model = Membership
    extra = 0
    readonly_fields = ("created_at",)


@admin.register(Space)
class SpaceAdmin(admin.ModelAdmin):
    list_display = ("name", "kind", "created_by", "created_at")
    list_filter = ("kind",)
    search_fields = ("name", "created_by__username")
    readonly_fields = ("created_at", "updated_at")
    inlines = (MembershipInline,)


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ("space", "user", "role", "created_at")
    list_filter = ("role", "space__kind")
    search_fields = ("space__name", "user__username")
    readonly_fields = ("created_at",)


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = (
        "space",
        "invited_user",
        "invited_by",
        "status",
        "created_at",
    )
    list_filter = ("status",)
    search_fields = (
        "space__name",
        "invited_user__username",
        "invited_by__username",
    )
    readonly_fields = ("created_at", "responded_at")
