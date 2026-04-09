from django.contrib import admin

from .models import (
    Accessory, AccessoryType, Brand, CPU, Device,
    DeviceCategory, DeviceModel, DeviceSpec, Flag, GPU, OperatingSystem,
)


# ── Inline for DeviceSpec ──────────────────────────────────────────────────────

class DeviceSpecInline(admin.TabularInline):
    model  = DeviceSpec
    extra  = 1
    fields = ('spec_name', 'spec_value')

    def has_add_permission(self, request, obj=None):
        return request.user.has_perm('inventory.add_devicespec')

    def has_change_permission(self, request, obj=None):
        return request.user.has_perm('inventory.change_devicespec')

    def has_delete_permission(self, request, obj=None):
        return request.user.has_perm('inventory.delete_devicespec')


# ── Lookup-table admins (shared pattern) ──────────────────────────────────────

class LookupAdmin(admin.ModelAdmin):
    """Base admin for simple lookup tables (Brand, DeviceCategory, etc.)."""
    readonly_fields = ('created_date', 'updated_date')

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(DeviceCategory)
class DeviceCategoryAdmin(LookupAdmin):
    list_display  = ('name', 'created_by', 'created_date')
    search_fields = ('name',)

    def has_add_permission(self, request):
        return request.user.has_perm('inventory.add_devicecategory')

    def has_change_permission(self, request, obj=None):
        return request.user.has_perm('inventory.change_devicecategory')

    def has_delete_permission(self, request, obj=None):
        return request.user.has_perm('inventory.delete_devicecategory')

    def has_view_permission(self, request, obj=None):
        return request.user.has_perm('inventory.view_devicecategory')


@admin.register(Brand)
class BrandAdmin(LookupAdmin):
    list_display  = ('name', 'created_by', 'created_date')
    search_fields = ('name',)

    def has_add_permission(self, request):
        return request.user.has_perm('inventory.add_brand')

    def has_change_permission(self, request, obj=None):
        return request.user.has_perm('inventory.change_brand')

    def has_delete_permission(self, request, obj=None):
        return request.user.has_perm('inventory.delete_brand')

    def has_view_permission(self, request, obj=None):
        return request.user.has_perm('inventory.view_brand')


@admin.register(DeviceModel)
class DeviceModelAdmin(LookupAdmin):
    list_display  = ('name', 'brand', 'category', 'created_date')
    list_filter   = ('brand', 'category')
    search_fields = ('name',)

    def has_add_permission(self, request):
        return request.user.has_perm('inventory.add_devicemodel')

    def has_change_permission(self, request, obj=None):
        return request.user.has_perm('inventory.change_devicemodel')

    def has_delete_permission(self, request, obj=None):
        return request.user.has_perm('inventory.delete_devicemodel')

    def has_view_permission(self, request, obj=None):
        return request.user.has_perm('inventory.view_devicemodel')


@admin.register(CPU)
class CPUAdmin(LookupAdmin):
    list_display  = ('name', 'brand', 'created_date')
    list_filter   = ('brand',)
    search_fields = ('name',)

    def has_add_permission(self, request):
        return request.user.has_perm('inventory.add_cpu')

    def has_change_permission(self, request, obj=None):
        return request.user.has_perm('inventory.change_cpu')

    def has_delete_permission(self, request, obj=None):
        return request.user.has_perm('inventory.delete_cpu')

    def has_view_permission(self, request, obj=None):
        return request.user.has_perm('inventory.view_cpu')


@admin.register(GPU)
class GPUAdmin(LookupAdmin):
    list_display  = ('name', 'brand', 'created_date')
    list_filter   = ('brand',)
    search_fields = ('name',)

    def has_add_permission(self, request):
        return request.user.has_perm('inventory.add_gpu')

    def has_change_permission(self, request, obj=None):
        return request.user.has_perm('inventory.change_gpu')

    def has_delete_permission(self, request, obj=None):
        return request.user.has_perm('inventory.delete_gpu')

    def has_view_permission(self, request, obj=None):
        return request.user.has_perm('inventory.view_gpu')


@admin.register(OperatingSystem)
class OperatingSystemAdmin(LookupAdmin):
    list_display  = ('name', 'created_by', 'created_date')
    search_fields = ('name',)

    def has_add_permission(self, request):
        return request.user.has_perm('inventory.add_operatingsystem')

    def has_change_permission(self, request, obj=None):
        return request.user.has_perm('inventory.change_operatingsystem')

    def has_delete_permission(self, request, obj=None):
        return request.user.has_perm('inventory.delete_operatingsystem')

    def has_view_permission(self, request, obj=None):
        return request.user.has_perm('inventory.view_operatingsystem')


@admin.register(Flag)
class FlagAdmin(LookupAdmin):
    list_display  = ('name', 'created_by', 'created_date')
    search_fields = ('name',)

    def has_add_permission(self, request):
        return request.user.has_perm('inventory.add_flag')

    def has_change_permission(self, request, obj=None):
        return request.user.has_perm('inventory.change_flag')

    def has_delete_permission(self, request, obj=None):
        return request.user.has_perm('inventory.delete_flag')

    def has_view_permission(self, request, obj=None):
        return request.user.has_perm('inventory.view_flag')


# ── Device ─────────────────────────────────────────────────────────────────────

@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display  = ('serial_number', 'category', 'brand', 'device_model',
                     'site', 'flag', 'maintenance_mode', 'created_date')
    list_filter   = ('category', 'brand', 'site', 'flag', 'maintenance_mode')
    search_fields = ('serial_number',)
    readonly_fields = ('created_date', 'updated_date')
    inlines       = [DeviceSpecInline]

    fieldsets = (
        ('Identity',     {'fields': ('serial_number', 'category', 'brand', 'device_model', 'site', 'flag')}),
        ('Compute specs', {'fields': ('cpu', 'gpu', 'ram_size_gb', 'hdd_storage_gb', 'ssd_storage_gb', 'operating_system'),
                           'classes': ('collapse',)}),
        ('Display specs', {'fields': ('screen_size_inch', 'ports_number'), 'classes': ('collapse',)}),
        ('Status',       {'fields': ('maintenance_mode',)}),
        ('Audit',        {'fields': ('created_by', 'created_date', 'updated_date', 'deleted_date')}),
    )

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    # ── RBAC gates ────────────────────────────────────────────────────────────

    def has_add_permission(self, request):
        return request.user.has_perm('inventory.add_device')

    def has_change_permission(self, request, obj=None):
        return request.user.has_perm('inventory.change_device')

    def has_delete_permission(self, request, obj=None):
        return request.user.has_perm('inventory.delete_device')

    def has_view_permission(self, request, obj=None):
        return request.user.has_perm('inventory.view_device')

    def get_fields(self, request, obj=None):
        """
        Hide hardware spec fields from users who lack view_device_specs.
        """
        fields = super().get_fields(request, obj)
        if not request.user.has_perm('inventory.view_device_specs'):
            hidden = {'cpu', 'gpu', 'ram_size_gb', 'hdd_storage_gb',
                      'ssd_storage_gb', 'operating_system', 'screen_size_inch', 'ports_number'}
            fields = [f for f in fields if f not in hidden]
        return fields


# ── Accessories ───────────────────────────────────────────────────────────────

@admin.register(AccessoryType)
class AccessoryTypeAdmin(LookupAdmin):
    list_display  = ('name', 'created_by', 'created_date')
    search_fields = ('name',)

    def has_add_permission(self, request):
        return request.user.has_perm('inventory.add_accessorytype')

    def has_change_permission(self, request, obj=None):
        return request.user.has_perm('inventory.change_accessorytype')

    def has_delete_permission(self, request, obj=None):
        return request.user.has_perm('inventory.delete_accessorytype')

    def has_view_permission(self, request, obj=None):
        return request.user.has_perm('inventory.view_accessorytype')


@admin.register(Accessory)
class AccessoryAdmin(admin.ModelAdmin):
    list_display  = ('accessory_type', 'serial_number', 'brand', 'site', 'flag', 'device')
    list_filter   = ('accessory_type', 'site', 'flag')
    search_fields = ('serial_number',)
    readonly_fields = ('created_date', 'updated_date')

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def has_add_permission(self, request):
        return request.user.has_perm('inventory.add_accessory')

    def has_change_permission(self, request, obj=None):
        return request.user.has_perm('inventory.change_accessory')

    def has_delete_permission(self, request, obj=None):
        return request.user.has_perm('inventory.delete_accessory')

    def has_view_permission(self, request, obj=None):
        return request.user.has_perm('inventory.view_accessory')