from django.contrib import admin

from .models import Task, TaskAssignment


class TaskAssignmentInline(admin.TabularInline):
    model = TaskAssignment
    extra = 0


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "space", "status", "priority", "due_date")
    list_filter = ("status", "priority", "space")
    search_fields = ("title", "description")
    inlines = (TaskAssignmentInline,)
