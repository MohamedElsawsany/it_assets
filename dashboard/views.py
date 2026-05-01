from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from accounts.models import User
from inventory.models import Device, DeviceFlag
from assignments.models import DeviceAssignment
from employees.models import Employee
from maintenance.models import MaintenanceRecord


@login_required
def dashboard(request):
    stats = {
        'total_users':      User.objects.filter(deleted_date__isnull=True).count(),
        'active_users':     User.objects.filter(is_active=True, deleted_date__isnull=True).count(),
        'total_devices':    Device.objects.filter(deleted_date__isnull=True).count(),
        'assigned_devices': DeviceAssignment.objects.filter(returned_date__isnull=True).count(),
        'open_maintenance': MaintenanceRecord.objects.filter(returned_date__isnull=True).count(),
        'total_employees':  Employee.objects.filter(deleted_date__isnull=True).count(),
    }

    # Device flag breakdown
    flag_counts_qs = (
        Device.objects
        .filter(deleted_date__isnull=True)
        .values('flag')
        .annotate(count=Count('id'))
    )
    flag_label_map = dict(DeviceFlag.choices)
    flag_color_map = {
        DeviceFlag.AVAILABLE:         '#16a34a',
        DeviceFlag.ASSIGNED:          '#2563eb',
        DeviceFlag.LOST:              '#dc2626',
        DeviceFlag.RETIRED:           '#6b7280',
        DeviceFlag.UNDER_MAINTENANCE: '#ea580c',
    }
    total_devices = stats['total_devices'] or 1  # avoid div-by-zero
    flag_breakdown = [
        {
            'flag':    row['flag'],
            'label':   flag_label_map.get(row['flag'], row['flag']),
            'count':   row['count'],
            'color':   flag_color_map.get(row['flag'], '#6b7280'),
            'percent': round(row['count'] / total_devices * 100),
        }
        for row in flag_counts_qs
    ]
    flag_breakdown.sort(key=lambda x: -x['count'])

    # Recent active assignments
    recent_assignments = (
        DeviceAssignment.objects
        .filter(returned_date__isnull=True)
        .select_related('device', 'device__device_model', 'device__category', 'employee')
        .order_by('-assigned_date')[:8]
    )

    # Open maintenance records
    open_maintenance = (
        MaintenanceRecord.objects
        .filter(returned_date__isnull=True)
        .select_related('device', 'device__device_model')
        .order_by('-sent_date')[:8]
    )

    return render(request, 'dashboard/index.html', {
        'stats':              stats,
        'flag_breakdown':     flag_breakdown,
        'recent_assignments': recent_assignments,
        'open_maintenance':   open_maintenance,
    })
