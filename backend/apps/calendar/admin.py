from django.contrib import admin

from .models import CalendarEvent


@admin.register(CalendarEvent)
class CalendarEventAdmin(admin.ModelAdmin):
    list_display = ("title", "space", "all_day", "date", "start_at", "color")
    list_filter = ("all_day", "color", "space")
    search_fields = ("title", "description", "location")
