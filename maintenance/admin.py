from django.contrib import admin

from .models import MaintenanceRecord


@admin.register(MaintenanceRecord)
class MaintenanceRecordAdmin(admin.ModelAdmin):
    list_display  = ('device', 'maintenance_type', 'sent_date', 'returned_date',
                     'vendor_name', 'is_open', 'created_by')
    list_filter   = ('maintenance_type', 'returned_date')
    search_fields = ('device__serial_number', 'vendor_name')
    readonly_fields = ('created_date', 'updated_date')

    fieldsets = (
        ('Device',      {'fields': ('device',)}),
        ('Issue',       {'fields': ('issue_description', 'maintenance_type', 'vendor_name')}),
        ('Timeline',    {'fields': ('sent_date', 'returned_date')}),
        ('Resolution',  {'fields': ('resolution_notes', 'cost')}),
        ('Audit',       {'fields': ('created_by', 'created_date', 'updated_date')}),
    )

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    # ── RBAC gates ────────────────────────────────────────────────────────────

    def has_add_permission(self, request):
        return request.user.has_perm('maintenance.add_maintenancerecord')

    def has_change_permission(self, request, obj=None):
        return (request.user.has_perm('maintenance.change_maintenancerecord') or
                request.user.has_perm('maintenance.close_maintenancerecord'))

    def has_delete_permission(self, request, obj=None):
        return request.user.has_perm('maintenance.delete_maintenancerecord')

    def has_view_permission(self, request, obj=None):
        return request.user.has_perm('maintenance.view_maintenancerecord')

    def get_fields(self, request, obj=None):
        """
        Hide the cost field from users without the view_cost permission.
        """
        fields = super().get_fields(request, obj)
        if not request.user.has_perm('maintenance.view_cost'):
            fields = [f for f in fields if f != 'cost']
        return fields