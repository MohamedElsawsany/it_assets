from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User
from .permissions import has_permission, Perms


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering        = ('email',)
    list_display    = ('email', 'first_name', 'last_name', 'site', 'is_active')
    list_filter     = ('is_active', 'site')
    search_fields   = ('email', 'first_name', 'last_name')

    fieldsets = (
        (None,            {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'site')}),
        ('Site Scope',    {'fields': ('site_scope', 'own_site', 'allowed_sites')}),
        ('Status',        {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        ('Audit',         {'fields': ('created_by', 'created_date', 'updated_date', 'deleted_date')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields':  ('email', 'first_name', 'last_name', 'site', 'password1', 'password2'),
        }),
    )

    readonly_fields = ('created_date', 'updated_date')

    def has_add_permission(self, request):
        return has_permission(request.user, Perms.USERS_CREATE)

    def has_change_permission(self, request, obj=None):
        return has_permission(request.user, Perms.USERS_EDIT)

    def has_delete_permission(self, request, obj=None):
        return has_permission(request.user, Perms.USERS_DELETE)

    def has_view_permission(self, request, obj=None):
        return has_permission(request.user, Perms.USERS_VIEW)
