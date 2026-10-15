from django.contrib import admin

from .models import Portal


@admin.register(Portal)
class PortalAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "destination_world",
        "energy_level",
        "stability",
        "creatures_count",
        "status",
    )
    list_filter = ("status",)
    search_fields = ("name", "destination_world")