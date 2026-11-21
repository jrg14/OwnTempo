from django.contrib import admin

from .models import WishItem


@admin.register(WishItem)
class WishItemAdmin(admin.ModelAdmin):
    list_display = ("title", "space", "kind", "status", "priority", "price")
    list_filter = ("status", "kind", "priority", "space")
    search_fields = ("title", "description")
