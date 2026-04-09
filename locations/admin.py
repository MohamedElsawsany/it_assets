from django.contrib import admin

from .models import Governorate, Site


@admin.register(Governorate)
class GovernorateAdmin(admin.ModelAdmin):
    list_display  = ('name', 'created_by', 'created_date')
    search_fields = ('name',)
    readonly_fields = ('created_date', 'updated_date')

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def has_add_permission(self, request):
        return request.user.has_perm('locations.add_governorate')

    def has_change_permission(self, request, obj=None):
        return request.user.has_perm('locations.change_governorate')

    def has_delete_permission(self, request, obj=None):
        return request.user.has_perm('locations.delete_governorate')

    def has_view_permission(self, request, obj=None):
        return request.user.has_perm('locations.view_governorate')


@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    list_display  = ('name', 'governorate', 'created_by', 'created_date')
    list_filter   = ('governorate',)
    search_fields = ('name',)
    readonly_fields = ('created_date', 'updated_date')

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def has_add_permission(self, request):
        return request.user.has_perm('locations.add_site')

    def has_change_permission(self, request, obj=None):
        return request.user.has_perm('locations.change_site')

    def has_delete_permission(self, request, obj=None):
        return request.user.has_perm('locations.delete_site')

    def has_view_permission(self, request, obj=None):
        return request.user.has_perm('locations.view_site')