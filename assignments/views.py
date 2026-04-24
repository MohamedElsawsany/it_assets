from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods
from django.db.models import Q

from accounts.permissions import permission_required, has_permission, Perms
from inventory.models import Device, DeviceFlag
from employees.models import Employee
from locations.models import Site
from .models import DeviceAssignment, DeviceTransfer
from .forms import AssignmentForm, ReturnDeviceForm, TransferForm


# ── Assignments ───────────────────────────────────────────────────────────────

@login_required
@permission_required(Perms.ASSIGNMENTS_VIEW)
def assignments_index(request):
    return render(request, 'assignments/index.html', {
        'devices':   Device.objects.filter(deleted_date__isnull=True).order_by('serial_number'),
        'employees': Employee.objects.filter(deleted_date__isnull=True).select_related('site').order_by('first_name'),
    })


@login_required
@permission_required(Perms.ASSIGNMENTS_VIEW)
def assignments_data(request):
    search   = request.GET.get('search', '').strip()
    status_f = request.GET.get('status', '').strip()
    qs = DeviceAssignment.objects.select_related(
        'device', 'device__brand', 'device__category',
        'employee', 'assigned_by'
    )
    if search:
        qs = qs.filter(
            Q(device__serial_number__icontains=search) |
            Q(employee__first_name__icontains=search) |
            Q(employee__last_name__icontains=search)
        )
    if status_f == 'active':
        qs = qs.filter(returned_date__isnull=True)
    elif status_f == 'returned':
        qs = qs.filter(returned_date__isnull=False)
    items = [
        {'id': a.pk,
         'device_id': a.device_id,
         'device_serial': a.device.serial_number,
         'device_label': f'{a.device.brand} {a.device.category}',
         'employee_id': a.employee_id,
         'employee_name': a.employee.full_name,
         'assigned_date': a.assigned_date.strftime('%Y-%m-%d'),
         'returned_date': a.returned_date.strftime('%Y-%m-%d') if a.returned_date else '',
         'is_active': a.is_active,
         'notes': a.notes or ''}
        for a in qs.order_by('-assigned_date')
    ]
    return JsonResponse({'success': True, 'items': items, 'total': len(items)})


@login_required
def assignment_detail(request, pk):
    if not has_permission(request.user, Perms.ASSIGNMENTS_VIEW):
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)
    a = get_object_or_404(DeviceAssignment.objects.select_related('device', 'employee', 'assigned_by'), pk=pk)
    return JsonResponse({'success': True, 'item': {
        'id': a.pk,
        'device_id': a.device_id,       'device_serial': a.device.serial_number,
        'employee_id': a.employee_id,   'employee_name': a.employee.full_name,
        'assigned_date': a.assigned_date.strftime('%Y-%m-%dT%H:%M'),
        'returned_date': a.returned_date.strftime('%Y-%m-%dT%H:%M') if a.returned_date else '',
        'is_active': a.is_active,
        'notes': a.notes or '',
        'assigned_by': a.assigned_by.full_name,
        'created_date': a.created_date.strftime('%Y-%m-%d %H:%M'),
        'updated_date': a.updated_date.strftime('%Y-%m-%d %H:%M') if a.updated_date else '',
    }})


@login_required
def transfer_detail(request, pk):
    if not has_permission(request.user, Perms.TRANSFERS_VIEW):
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)
    t = get_object_or_404(DeviceTransfer.objects.select_related('device', 'from_site', 'to_site', 'transferred_by'), pk=pk)
    return JsonResponse({'success': True, 'item': {
        'id': t.pk,
        'device_serial': t.device.serial_number,
        'from_site_name': t.from_site.name,
        'to_site_name': t.to_site.name,
        'transfer_date': t.transfer_date.strftime('%Y-%m-%d %H:%M'),
        'notes': t.notes or '',
        'transferred_by': t.transferred_by.full_name,
        'created_date': t.created_date.strftime('%Y-%m-%d %H:%M'),
    }})


@login_required
@require_http_methods(['POST'])
def assignment_create(request):
    if not has_permission(request.user, Perms.ASSIGNMENTS_CREATE):
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)
    form = AssignmentForm(request.POST)
    if form.is_valid():
        device = form.cleaned_data['device']
        if DeviceAssignment.objects.filter(device=device, returned_date__isnull=True).exists():
            return JsonResponse({'success': False, 'errors': {
                'device': [_('This device is already assigned and has not been returned yet.')]
            }})
        obj = form.save(commit=False)
        obj.assigned_by = request.user
        obj.save()
        obj.device.flag = DeviceFlag.ASSIGNED
        obj.device.save(update_fields=['flag'])
        return JsonResponse({'success': True, 'message': _('Assignment created successfully.')})
    errors = {f: [str(e) for e in v] for f, v in form.errors.items()}
    return JsonResponse({'success': False, 'errors': errors})


@login_required
@require_http_methods(['POST'])
def assignment_edit(request, pk):
    if not has_permission(request.user, Perms.ASSIGNMENTS_EDIT):
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)
    a = get_object_or_404(DeviceAssignment, pk=pk)
    form = AssignmentForm(request.POST, instance=a)
    if form.is_valid():
        form.save()
        return JsonResponse({'success': True, 'message': _('Assignment updated successfully.')})
    errors = {f: [str(e) for e in v] for f, v in form.errors.items()}
    return JsonResponse({'success': False, 'errors': errors})


@login_required
@require_http_methods(['POST'])
def assignment_return(request, pk):
    if not has_permission(request.user, Perms.ASSIGNMENTS_RETURN):
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)
    a = get_object_or_404(DeviceAssignment, pk=pk)
    if not a.is_active:
        return JsonResponse({'success': False, 'message': _('Assignment is already returned.')})
    form = ReturnDeviceForm(request.POST)
    if form.is_valid():
        a.returned_date = form.cleaned_data['returned_date']
        if form.cleaned_data.get('notes'):
            a.notes = (a.notes or '') + '\n[Return] ' + form.cleaned_data['notes']
        a.save()
        a.device.flag = DeviceFlag.AVAILABLE
        a.device.save(update_fields=['flag'])
        return JsonResponse({'success': True, 'message': _('Device returned successfully.')})
    errors = {f: [str(e) for e in v] for f, v in form.errors.items()}
    return JsonResponse({'success': False, 'errors': errors})


@login_required
@require_http_methods(['POST'])
def assignment_delete(request, pk):
    if not has_permission(request.user, Perms.ASSIGNMENTS_DELETE):
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)
    a = get_object_or_404(DeviceAssignment, pk=pk)
    a.delete()
    return JsonResponse({'success': True, 'message': _('Assignment deleted successfully.')})


# ── Transfers ─────────────────────────────────────────────────────────────────

@login_required
@permission_required(Perms.TRANSFERS_VIEW)
def transfers_index(request):
    return render(request, 'assignments/transfers.html', {
        'devices': Device.objects.filter(deleted_date__isnull=True).order_by('serial_number'),
        'sites':   Site.objects.filter(deleted_date__isnull=True).order_by('name'),
    })


@login_required
@permission_required(Perms.TRANSFERS_VIEW)
def transfers_data(request):
    search = request.GET.get('search', '').strip()
    qs = DeviceTransfer.objects.select_related(
        'device', 'from_site', 'to_site', 'transferred_by'
    )
    if search:
        qs = qs.filter(
            Q(device__serial_number__icontains=search) |
            Q(from_site__name__icontains=search) |
            Q(to_site__name__icontains=search)
        )
    items = [
        {'id': t.pk,
         'device_id': t.device_id,
         'device_serial': t.device.serial_number,
         'from_site_id': t.from_site_id,
         'from_site_name': t.from_site.name,
         'to_site_id': t.to_site_id,
         'to_site_name': t.to_site.name,
         'transfer_date': t.transfer_date.strftime('%Y-%m-%d'),
         'notes': t.notes or '',
         'transferred_by': t.transferred_by.full_name}
        for t in qs.order_by('-transfer_date')
    ]
    return JsonResponse({'success': True, 'items': items, 'total': len(items)})


@login_required
@require_http_methods(['POST'])
def transfer_create(request):
    if not has_permission(request.user, Perms.TRANSFERS_CREATE):
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)
    form = TransferForm(request.POST)
    if form.is_valid():
        obj = form.save(commit=False)
        obj.transferred_by = request.user
        obj.save()
        return JsonResponse({'success': True, 'message': _('Transfer recorded successfully.')})
    errors = {f: [str(e) for e in v] for f, v in form.errors.items()}
    return JsonResponse({'success': False, 'errors': errors})


@login_required
@require_http_methods(['POST'])
def transfer_delete(request, pk):
    if not has_permission(request.user, Perms.TRANSFERS_DELETE):
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)
    t = get_object_or_404(DeviceTransfer, pk=pk)
    t.delete()
    return JsonResponse({'success': True, 'message': _('Transfer deleted successfully.')})
