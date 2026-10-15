from django.contrib import admin

from .models import Portal, PortalHistory


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