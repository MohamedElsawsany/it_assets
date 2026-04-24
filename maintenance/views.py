from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods
from django.db.models import Q

PAGE_SIZE = 10

from accounts.permissions import permission_required, has_permission, Perms
from inventory.models import Device, DeviceFlag
from .models import MaintenanceRecord
from .forms import MaintenanceForm, CloseMaintenanceForm


@login_required
@permission_required(Perms.MAINTENANCE_VIEW)
def maintenance_index(request):
    return render(request, 'maintenance/index.html', {
        'devices': Device.objects.filter(
            deleted_date__isnull=True
        ).select_related('category', 'brand').order_by('serial_number'),
        'type_choices': MaintenanceRecord.MaintenanceType.choices,
    })


@login_required
@permission_required(Perms.MAINTENANCE_VIEW)
def maintenance_data(request):
    search   = request.GET.get('search', '').strip()
    status_f = request.GET.get('status', '').strip()
    type_f   = request.GET.get('type', '').strip()
    show_cost = has_permission(request.user, Perms.MAINTENANCE_VIEW_COST)

    qs = MaintenanceRecord.objects.select_related(
        'device', 'device__category', 'device__brand'
    )
    if search:
        qs = qs.filter(
            Q(device__serial_number__icontains=search) |
            Q(vendor_name__icontains=search) |
            Q(issue_description__icontains=search)
        )
    if status_f == 'open':
        qs = qs.filter(returned_date__isnull=True)
    elif status_f == 'closed':
        qs = qs.filter(returned_date__isnull=False)
    if type_f:
        qs = qs.filter(maintenance_type=type_f)

    qs = qs.order_by('-sent_date')
    paginator = Paginator(qs, PAGE_SIZE)
    try:
        page_num = int(request.GET.get('page', 1))
    except (ValueError, TypeError):
        page_num = 1
    page_obj  = paginator.get_page(page_num)
    items = []
    for r in page_obj:
        item = {
            'id': r.pk,
            'device_id': r.device_id,
            'device_serial': r.device.serial_number,
            'maintenance_type': r.maintenance_type,
            'maintenance_type_display': r.get_maintenance_type_display(),
            'vendor_name': r.vendor_name or '',
            'issue_description': r.issue_description[:80],
            'sent_date': r.sent_date.strftime('%Y-%m-%d'),
            'returned_date': r.returned_date.strftime('%Y-%m-%d') if r.returned_date else '',
            'is_open': r.is_open,
        }
        if show_cost:
            item['cost'] = str(r.cost) if r.cost is not None else ''
        items.append(item)
    return JsonResponse({'success': True, 'items': items, 'total': paginator.count,
                         'page': page_obj.number, 'num_pages': paginator.num_pages,
                         'show_cost': show_cost})


@login_required
def maintenance_detail(request, pk):
    if not has_permission(request.user, Perms.MAINTENANCE_VIEW):
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)
    show_cost = has_permission(request.user, Perms.MAINTENANCE_VIEW_COST)
    rec = get_object_or_404(MaintenanceRecord.objects.select_related('device'), pk=pk)
    item = {
        'id': rec.pk,
        'device_id': rec.device_id, 'device_serial': rec.device.serial_number,
        'issue_description': rec.issue_description,
        'maintenance_type': rec.maintenance_type,
        'maintenance_type_display': rec.get_maintenance_type_display(),
        'vendor_name': rec.vendor_name or '',
        'sent_date': rec.sent_date.strftime('%Y-%m-%dT%H:%M'),
        'returned_date': rec.returned_date.strftime('%Y-%m-%dT%H:%M') if rec.returned_date else '',
        'resolution_notes': rec.resolution_notes or '',
        'is_open': rec.is_open,
    }
    if show_cost:
        item['cost'] = str(rec.cost) if rec.cost is not None else ''
    return JsonResponse({'success': True, 'item': item, 'show_cost': show_cost})


@login_required
@require_http_methods(['POST'])
def maintenance_create(request):
    if not has_permission(request.user, Perms.MAINTENANCE_CREATE):
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)
    form = MaintenanceForm(request.POST)
    if form.is_valid():
        rec = form.save(commit=False)
        rec.created_by = request.user
        device = rec.device
        # Block if device already has an open maintenance record
        if device.maintenance_records.filter(returned_date__isnull=True).exists():
            return JsonResponse({
                'success': False,
                'message': _('This device already has an open maintenance record. Please close it before creating a new one.'),
            })
        # Save the device's current flag so we can restore it when this record is closed
        rec.previous_flag = device.flag
        rec.save()
        # Put the device under maintenance
        device.flag = DeviceFlag.UNDER_MAINTENANCE
        device.maintenance_mode = True
        device.save()
        return JsonResponse({'success': True, 'message': _('Maintenance record created successfully.')})
    errors = {f: [str(e) for e in v] for f, v in form.errors.items()}
    return JsonResponse({'success': False, 'errors': errors})


@login_required
@require_http_methods(['POST'])
def maintenance_edit(request, pk):
    if not has_permission(request.user, Perms.MAINTENANCE_EDIT):
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)
    rec = get_object_or_404(MaintenanceRecord, pk=pk)
    form = MaintenanceForm(request.POST, instance=rec)
    if form.is_valid():
        form.save()
        return JsonResponse({'success': True, 'message': _('Maintenance record updated successfully.')})
    errors = {f: [str(e) for e in v] for f, v in form.errors.items()}
    return JsonResponse({'success': False, 'errors': errors})


def _restore_device_flag(device, previous_flag):
    """Restore device flag after closing/deleting the last open maintenance record."""
    # If a valid previous flag was stored, restore it; otherwise fall back to assignment status
    if previous_flag and previous_flag != DeviceFlag.UNDER_MAINTENANCE:
        device.flag = previous_flag
    else:
        has_active = device.assignments.filter(returned_date__isnull=True).exists()
        device.flag = DeviceFlag.ASSIGNED if has_active else DeviceFlag.AVAILABLE
    device.maintenance_mode = False
    device.save()


@login_required
@require_http_methods(['POST'])
def maintenance_close(request, pk):
    if not has_permission(request.user, Perms.MAINTENANCE_CLOSE):
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)
    rec = get_object_or_404(MaintenanceRecord, pk=pk)
    if not rec.is_open:
        return JsonResponse({'success': False, 'message': _('Record is already closed.')})
    form = CloseMaintenanceForm(request.POST)
    if form.is_valid():
        rec.returned_date    = form.cleaned_data['returned_date']
        rec.resolution_notes = form.cleaned_data.get('resolution_notes', '')
        if has_permission(request.user, Perms.MAINTENANCE_VIEW_COST):
            rec.cost = form.cleaned_data.get('cost')
        rec.save()
        # Restore device flag if this was the last open record for the device
        other_open = rec.device.maintenance_records.filter(returned_date__isnull=True).exclude(pk=rec.pk).exists()
        if not other_open:
            _restore_device_flag(rec.device, rec.previous_flag)
        return JsonResponse({'success': True, 'message': _('Maintenance record closed successfully.')})
    errors = {f: [str(e) for e in v] for f, v in form.errors.items()}
    return JsonResponse({'success': False, 'errors': errors})


@login_required
@require_http_methods(['POST'])
def maintenance_delete(request, pk):
    if not has_permission(request.user, Perms.MAINTENANCE_DELETE):
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)
    rec = get_object_or_404(MaintenanceRecord, pk=pk)
    # If the record is open, restore device flag when it's the last open record
    if rec.is_open:
        other_open = rec.device.maintenance_records.filter(returned_date__isnull=True).exclude(pk=rec.pk).exists()
        if not other_open:
            _restore_device_flag(rec.device, rec.previous_flag)
    rec.delete()
    return JsonResponse({'success': True, 'message': _('Maintenance record deleted successfully.')})
