from django.contrib import admin

from .models import Department, Employee


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display  = ('name', 'created_by', 'created_date')
    search_fields = ('name',)
    readonly_fields = ('created_date', 'updated_date')

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def has_add_permission(self, request):
        return request.user.has_perm('employees.add_department')

    def has_change_permission(self, request, obj=None):
        return request.user.has_perm('employees.change_department')

    def has_delete_permission(self, request, obj=None):
        return request.user.has_perm('employees.delete_department')

    def has_view_permission(self, request, obj=None):
        return request.user.has_perm('employees.view_department')


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display  = ('full_name', 'employee_card_id', 'department', 'site', 'created_date')
    list_filter   = ('department', 'site')
    search_fields = ('first_name', 'last_name', 'employee_card_id')
    readonly_fields = ('created_date', 'updated_date')

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def has_add_permission(self, request):
        return request.user.has_perm('employees.add_employee')

    def has_change_permission(self, request, obj=None):
        return request.user.has_perm('employees.change_employee')

    def has_delete_permission(self, request, obj=None):
        return request.user.has_perm('employees.delete_employee')

    def has_view_permission(self, request, obj=None):
        return request.user.has_perm('employees.view_employee')