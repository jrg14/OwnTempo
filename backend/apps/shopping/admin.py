from django.contrib import admin

from .models import ShoppingItem, ShoppingList


class ShoppingItemInline(admin.TabularInline):
    model = ShoppingItem
    extra = 0


@admin.register(ShoppingList)
class ShoppingListAdmin(admin.ModelAdmin):
    list_display = ("name", "space", "created_by", "updated_at")
    list_filter = ("space",)
    search_fields = ("name",)
    inlines = (ShoppingItemInline,)


@admin.register(ShoppingItem)
class ShoppingItemAdmin(admin.ModelAdmin):
    list_display = ("name", "shopping_list", "status", "position")
    list_filter = ("status", "shopping_list__space")
    search_fields = ("name", "note")
