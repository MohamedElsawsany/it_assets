from django.contrib import admin

from .models import DeliveredDeviceHistory, DeviceAssignment, DeviceTransfer


@admin.register(DeviceAssignment)
class DeviceAssignmentAdmin(admin.ModelAdmin):
    list_display  = ('device', 'employee', 'assigned_date', 'returned_date', 'assigned_by', 'is_active')
    list_filter   = ('employee__site',)
    search_fields = ('device__serial_number', 'employee__first_name', 'employee__last_name')
    readonly_fields = ('created_date', 'updated_date')

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.assigned_by = request.user
        super().save_model(request, obj, form, change)

    def has_add_permission(self, request):
        return request.user.has_perm('assignments.add_deviceassignment')

    def has_change_permission(self, request, obj=None):
        # Returning a device uses change_deviceassignment OR the custom return_device perm
        return (request.user.has_perm('assignments.change_deviceassignment') or
                request.user.has_perm('assignments.return_device'))

    def has_delete_permission(self, request, obj=None):
        return request.user.has_perm('assignments.delete_deviceassignment')

    def has_view_permission(self, request, obj=None):
        return request.user.has_perm('assignments.view_deviceassignment')


@admin.register(DeviceTransfer)
class DeviceTransferAdmin(admin.ModelAdmin):
    list_display  = ('device', 'from_site', 'to_site', 'transfer_date', 'transferred_by')
    list_filter   = ('from_site', 'to_site')
    search_fields = ('device__serial_number',)
    readonly_fields = ('created_date',)

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.transferred_by = request.user
        super().save_model(request, obj, form, change)

    def has_add_permission(self, request):
        return request.user.has_perm('assignments.add_devicetransfer')

    def has_change_permission(self, request, obj=None):
        return (request.user.has_perm('assignments.change_devicetransfer') or
                request.user.has_perm('assignments.approve_transfer'))

    def has_delete_permission(self, request, obj=None):
        return request.user.has_perm('assignments.delete_devicetransfer')

    def has_view_permission(self, request, obj=None):
        return request.user.has_perm('assignments.view_devicetransfer')


@admin.register(DeliveredDeviceHistory)
class DeliveredDeviceHistoryAdmin(admin.ModelAdmin):
    """Read-only ledger — nobody edits history rows."""
    list_display  = ('serial_number', 'category_name', 'brand_name', 'site_name',
                     'governorate_name', 'employee', 'created_date')
    list_filter   = ('site_name', 'governorate_name', 'category_name')
    search_fields = ('serial_number', 'site_name')
    readonly_fields = [f.name for f in DeliveredDeviceHistory._meta.get_fields()
                       if hasattr(f, 'name')]

    def has_add_permission(self, request):
        return False   # snapshots are written by application logic only

    def has_change_permission(self, request, obj=None):
        return False   # history is immutable

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser   # super_admin only, for emergencies

    def has_view_permission(self, request, obj=None):
        return request.user.has_perm('assignments.view_delivereddevicehistory')