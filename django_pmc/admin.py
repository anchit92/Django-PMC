from django.contrib import admin
from .models import TaskLock


@admin.register(TaskLock)
class TaskLockAdmin(admin.ModelAdmin):
    list_display = ("name", "locked_until")
    search_fields = ("name",)
    ordering = ("name",)
