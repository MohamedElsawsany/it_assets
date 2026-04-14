from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from accounts.models import User
from inventory.models import Device
from assignments.models import DeviceAssignment
from employees.models import Employee
from maintenance.models import MaintenanceRecord


@login_required
def dashboard(request):
    stats = {
        'total_users': User.objects.filter(deleted_date__isnull=True).count(),
        'active_users': User.objects.filter(is_active=True, deleted_date__isnull=True).count(),
        'total_devices': Device.objects.filter(deleted_date__isnull=True).count(),
        'assigned_devices': DeviceAssignment.objects.filter(returned_date__isnull=True).count(),
        'open_maintenance': MaintenanceRecord.objects.filter(returned_date__isnull=True).count(),
        'total_employees': Employee.objects.filter(deleted_date__isnull=True).count(),
    }
    return render(request, 'dashboard/index.html', {'stats': stats})
