from django.contrib import admin

from .models import EventLog, Portal, PortalHistory


class PortalHistoryInline(admin.TabularInline):
    model = PortalHistory
    extra = 0
    can_delete = False
    readonly_fields = ("changed_at", "field_label", "old_value", "new_value")
    fields = ("changed_at", "field_label", "old_value", "new_value")

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Portal)
class PortalAdmin(admin.ModelAdmin):
    list_display = (
        "name", "destination_world", "energy_level", "stability",
        "creatures_count", "collapse_at", "status", "under_question",
    )
    list_filter = ("status", "under_question")
    search_fields = ("name", "destination_world")
    inlines = [PortalHistoryInline]

@admin.register(EventLog)
class EventLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "portal_name", "action_label", "outcome", "message")
    list_filter = ("outcome", "action")
    search_fields = ("portal_name", "message")