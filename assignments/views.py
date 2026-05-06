from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods
from django.db.models import Q

PAGE_SIZE = 10

from accounts.permissions import permission_required, has_permission, Perms
from inventory.models import Device, Accessory, DeviceFlag
from employees.models import Employee
from locations.models import Site
from .models import DeviceAssignment, AccessoryAssignment, DeviceTransfer, AccessoryTransfer, TransferStatus
from .forms import AssignmentForm, AccessoryAssignmentForm, ReturnDeviceForm


# ── Assignments ───────────────────────────────────────────────────────────────

@login_required
@permission_required(Perms.ASSIGNMENTS_VIEW)
def assignments_index(request):
    return render(request, 'assignments/index.html')


@login_required
@permission_required(Perms.ASSIGNMENTS_VIEW)
def assignments_data(request):
    search   = request.GET.get('search', '').strip()
    status_f = request.GET.get('status', '').strip()
    qs = DeviceAssignment.objects.filter(
        device__site__in=request.user.get_allowed_sites(),
    ).select_related(
        'device', 'device__brand', 'device__category', 'device__device_model',
        'employee', 'assigned_by', 'returned_by',
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
    qs = qs.order_by('-assigned_date')
    paginator = Paginator(qs, PAGE_SIZE)
    try:
        page_num = int(request.GET.get('page', 1))
    except (ValueError, TypeError):
        page_num = 1
    page_obj  = paginator.get_page(page_num)
    items = [
        {'id': a.pk,
         'device_id': a.device_id,
         'device_serial': a.device.serial_number,
         'device_category': str(a.device.category),
         'device_brand': str(a.device.brand),
         'device_model': a.device.device_model.name,
         'employee_id': a.employee_id,
         'employee_name': a.employee.full_name,
         'assigned_date': a.assigned_date.strftime('%Y-%m-%d'),
         'assigned_by': a.assigned_by.full_name,
         'returned_date': a.returned_date.strftime('%Y-%m-%d') if a.returned_date else '',
         'returned_by': a.returned_by.full_name if a.returned_by else '',
         'is_active': a.is_active,
         'notes': a.notes or ''}
        for a in page_obj
    ]
    return JsonResponse({'success': True, 'items': items, 'total': paginator.count,
                         'page': page_obj.number, 'num_pages': paginator.num_pages})


@login_required
def assignment_detail(request, pk):
    if not has_permission(request.user, Perms.ASSIGNMENTS_VIEW):
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)
    a = get_object_or_404(
        DeviceAssignment.objects.filter(
            device__site__in=request.user.get_allowed_sites(),
        ).select_related(
            'device', 'device__brand', 'device__category', 'device__device_model',
            'employee', 'assigned_by', 'returned_by',
        ), pk=pk)
    return JsonResponse({'success': True, 'item': {
        'id': a.pk,
        'device_id': a.device_id,
        'device_serial': a.device.serial_number,
        'device_category': str(a.device.category),
        'device_brand': str(a.device.brand),
        'device_model': a.device.device_model.name,
        'employee_id': a.employee_id,
        'employee_name': a.employee.full_name,
        'assigned_date': a.assigned_date.strftime('%Y-%m-%dT%H:%M'),
        'returned_date': a.returned_date.strftime('%Y-%m-%dT%H:%M') if a.returned_date else '',
        'is_active': a.is_active,
        'notes': a.notes or '',
        'assigned_by': a.assigned_by.full_name,
        'returned_by': a.returned_by.full_name if a.returned_by else '',
        'created_date': a.created_date.strftime('%Y-%m-%d %I:%M %p'),
        'updated_date': a.updated_date.strftime('%Y-%m-%d %I:%M %p') if a.updated_date else '',
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
def assignment_return(request, pk):
    if not has_permission(request.user, Perms.ASSIGNMENTS_RETURN):
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)
    a = get_object_or_404(DeviceAssignment, pk=pk)
    if not a.is_active:
        return JsonResponse({'success': False, 'message': _('Assignment is already returned.')})
    form = ReturnDeviceForm(request.POST)
    if form.is_valid():
        a.returned_date = form.cleaned_data['returned_date']
        a.returned_by   = request.user
        if form.cleaned_data.get('notes'):
            a.notes = (a.notes or '') + '\n[Return] ' + form.cleaned_data['notes']
        a.save()
        a.device.flag = DeviceFlag.AVAILABLE
        a.device.save(update_fields=['flag'])
        return JsonResponse({'success': True, 'message': _('Device returned successfully.')})
    errors = {f: [str(e) for e in v] for f, v in form.errors.items()}
    return JsonResponse({'success': False, 'errors': errors})




# ── Accessory Assignments ─────────────────────────────────────────────────────

@login_required
@permission_required(Perms.ASSIGNMENTS_VIEW)
def acc_assignments_data(request):
    search   = request.GET.get('search', '').strip()
    status_f = request.GET.get('status', '').strip()
    qs = AccessoryAssignment.objects.filter(
        accessory__site__in=request.user.get_allowed_sites(),
    ).select_related(
        'accessory', 'accessory__accessory_type', 'accessory__brand',
        'employee', 'assigned_by', 'returned_by',
    )
    if search:
        qs = qs.filter(
            Q(accessory__serial_number__icontains=search) |
            Q(accessory__accessory_type__name__icontains=search) |
            Q(employee__first_name__icontains=search) |
            Q(employee__last_name__icontains=search)
        )
    if status_f == 'active':
        qs = qs.filter(returned_date__isnull=True)
    elif status_f == 'returned':
        qs = qs.filter(returned_date__isnull=False)
    qs = qs.order_by('-assigned_date')
    paginator = Paginator(qs, PAGE_SIZE)
    try:
        page_num = int(request.GET.get('page', 1))
    except (ValueError, TypeError):
        page_num = 1
    page_obj = paginator.get_page(page_num)
    items = [
        {'id': a.pk,
         'accessory_id': a.accessory_id,
         'accessory_type': a.accessory.accessory_type.name,
         'accessory_brand': a.accessory.brand.name if a.accessory.brand else '',
         'accessory_serial': a.accessory.serial_number or '',
         'employee_id': a.employee_id,
         'employee_name': a.employee.full_name,
         'assigned_date': a.assigned_date.strftime('%Y-%m-%d'),
         'assigned_by': a.assigned_by.full_name,
         'returned_date': a.returned_date.strftime('%Y-%m-%d') if a.returned_date else '',
         'returned_by': a.returned_by.full_name if a.returned_by else '',
         'is_active': a.is_active,
         'notes': a.notes or ''}
        for a in page_obj
    ]
    return JsonResponse({'success': True, 'items': items, 'total': paginator.count,
                         'page': page_obj.number, 'num_pages': paginator.num_pages})


@login_required
def acc_assignment_detail(request, pk):
    if not has_permission(request.user, Perms.ASSIGNMENTS_VIEW):
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)
    a = get_object_or_404(
        AccessoryAssignment.objects.filter(
            accessory__site__in=request.user.get_allowed_sites(),
        ).select_related(
            'accessory', 'accessory__accessory_type', 'accessory__brand',
            'employee', 'assigned_by', 'returned_by',
        ), pk=pk)
    return JsonResponse({'success': True, 'item': {
        'id': a.pk,
        'accessory_id': a.accessory_id,
        'accessory_type': a.accessory.accessory_type.name,
        'accessory_brand': a.accessory.brand.name if a.accessory.brand else '',
        'accessory_serial': a.accessory.serial_number or '',
        'employee_id': a.employee_id,
        'employee_name': a.employee.full_name,
        'assigned_date': a.assigned_date.strftime('%Y-%m-%dT%H:%M'),
        'returned_date': a.returned_date.strftime('%Y-%m-%dT%H:%M') if a.returned_date else '',
        'is_active': a.is_active,
        'notes': a.notes or '',
        'assigned_by': a.assigned_by.full_name,
        'returned_by': a.returned_by.full_name if a.returned_by else '',
        'created_date': a.created_date.strftime('%Y-%m-%d %I:%M %p'),
    }})


@login_required
@require_http_methods(['POST'])
def acc_assignment_create(request):
    if not has_permission(request.user, Perms.ASSIGNMENTS_CREATE):
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)
    form = AccessoryAssignmentForm(request.POST)
    if form.is_valid():
        accessory = form.cleaned_data['accessory']
        if AccessoryAssignment.objects.filter(accessory=accessory, returned_date__isnull=True).exists():
            return JsonResponse({'success': False, 'errors': {
                'accessory': [_('This accessory is already assigned and has not been returned yet.')]
            }})
        obj = form.save(commit=False)
        obj.assigned_by = request.user
        obj.save()
        obj.accessory.flag = DeviceFlag.ASSIGNED
        obj.accessory.save(update_fields=['flag'])
        return JsonResponse({'success': True, 'message': _('Accessory assigned successfully.')})
    errors = {f: [str(e) for e in v] for f, v in form.errors.items()}
    return JsonResponse({'success': False, 'errors': errors})


@login_required
@require_http_methods(['POST'])
def acc_assignment_return(request, pk):
    if not has_permission(request.user, Perms.ASSIGNMENTS_RETURN):
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)
    a = get_object_or_404(AccessoryAssignment, pk=pk)
    if not a.is_active:
        return JsonResponse({'success': False, 'message': _('Assignment is already returned.')})
    form = ReturnDeviceForm(request.POST)
    if form.is_valid():
        a.returned_date = form.cleaned_data['returned_date']
        a.returned_by   = request.user
        if form.cleaned_data.get('notes'):
            a.notes = (a.notes or '') + '\n[Return] ' + form.cleaned_data['notes']
        a.save()
        a.accessory.flag = DeviceFlag.AVAILABLE
        a.accessory.save(update_fields=['flag'])
        return JsonResponse({'success': True, 'message': _('Accessory returned successfully.')})
    errors = {f: [str(e) for e in v] for f, v in form.errors.items()}
    return JsonResponse({'success': False, 'errors': errors})


# ── Transfers ─────────────────────────────────────────────────────────────────

def _is_all_sites(user):
    from accounts.models import User as _User
    return user.is_superuser or getattr(user, 'site_scope', _User.SiteScope.OWN) == _User.SiteScope.ALL


@login_required
@permission_required(Perms.TRANSFERS_VIEW)
def transfers_index(request):
    allowed = request.user.get_allowed_sites()
    return render(request, 'assignments/transfers.html', {
        'my_sites':  allowed.filter(deleted_date__isnull=True).order_by('name'),
        'all_sites': Site.objects.filter(deleted_date__isnull=True).order_by('name'),
    })


# ── Device transfer list & detail ────────────────────────────────────────────

@login_required
@permission_required(Perms.TRANSFERS_VIEW)
def device_transfers_data(request):
    search   = request.GET.get('search', '').strip()
    status_f = request.GET.get('status', '').strip()
    allowed  = request.user.get_allowed_sites()
    allowed_ids = set(allowed.values_list('id', flat=True))
    all_sites   = _is_all_sites(request.user)

    qs = DeviceTransfer.objects.filter(
        Q(from_site__in=allowed) | Q(to_site__in=allowed)
    ).select_related('device', 'from_site', 'to_site', 'transferred_by', 'resolved_by')

    if search:
        qs = qs.filter(
            Q(device__serial_number__icontains=search) |
            Q(from_site__name__icontains=search) |
            Q(to_site__name__icontains=search)
        )
    if status_f in (TransferStatus.PENDING, TransferStatus.ACCEPTED, TransferStatus.REJECTED):
        qs = qs.filter(status=status_f)

    qs = qs.order_by('-transfer_date')
    paginator = Paginator(qs, PAGE_SIZE)
    try:
        page_num = int(request.GET.get('page', 1))
    except (ValueError, TypeError):
        page_num = 1
    page_obj = paginator.get_page(page_num)

    items = []
    for t in page_obj:
        is_pending = t.status == TransferStatus.PENDING
        can_ar = is_pending and (all_sites or t.to_site_id in allowed_ids)
        can_del = is_pending and (all_sites or t.from_site_id in allowed_ids)
        items.append({
            'id': t.pk,
            'device_id': t.device_id,
            'device_serial': t.device.serial_number,
            'from_site_name': t.from_site.name,
            'to_site_name': t.to_site.name,
            'transfer_date': t.transfer_date.strftime('%Y-%m-%d'),
            'status': t.status,
            'notes': t.notes or '',
            'transferred_by': t.transferred_by.full_name,
            'resolved_by': t.resolved_by.full_name if t.resolved_by else '',
            'resolved_date': t.resolved_date.strftime('%Y-%m-%d') if t.resolved_date else '',
            'can_accept': can_ar,
            'can_reject': can_ar,
            'can_delete': can_del,
        })
    return JsonResponse({'success': True, 'items': items, 'total': paginator.count,
                         'page': page_obj.number, 'num_pages': paginator.num_pages})


@login_required
def transfer_detail(request, pk):
    if not has_permission(request.user, Perms.TRANSFERS_VIEW):
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)
    allowed = request.user.get_allowed_sites()
    t = get_object_or_404(
        DeviceTransfer.objects.filter(
            Q(from_site__in=allowed) | Q(to_site__in=allowed),
        ).select_related('device', 'from_site', 'to_site', 'transferred_by', 'resolved_by'),
        pk=pk,
    )
    return JsonResponse({'success': True, 'item': {
        'id': t.pk,
        'device_serial': t.device.serial_number,
        'from_site_name': t.from_site.name,
        'to_site_name': t.to_site.name,
        'transfer_date': t.transfer_date.strftime('%Y-%m-%d %I:%M %p'),
        'status': t.status,
        'notes': t.notes or '',
        'transferred_by': t.transferred_by.full_name,
        'resolved_by': t.resolved_by.full_name if t.resolved_by else '',
        'resolved_date': t.resolved_date.strftime('%Y-%m-%d %I:%M %p') if t.resolved_date else '',
        'created_date': t.created_date.strftime('%Y-%m-%d %I:%M %p'),
    }})


# ── Device transfer create / accept / reject / delete ────────────────────────

@login_required
@require_http_methods(['POST'])
def device_transfer_create(request):
    if not has_permission(request.user, Perms.TRANSFERS_CREATE):
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)

    from django.utils import timezone
    from datetime import datetime

    allowed     = request.user.get_allowed_sites()
    allowed_ids = set(allowed.values_list('id', flat=True))

    device_ids    = request.POST.getlist('device_ids[]')
    to_site_id    = request.POST.get('to_site', '').strip()
    transfer_date = request.POST.get('transfer_date', '').strip()
    notes         = request.POST.get('notes', '').strip() or None

    if not device_ids:
        return JsonResponse({'success': False, 'message': _('Select at least one device.')})
    if not to_site_id:
        return JsonResponse({'success': False, 'message': _('Select a destination site.')})

    try:
        to_site = Site.objects.get(pk=to_site_id)
    except Site.DoesNotExist:
        return JsonResponse({'success': False, 'message': _('Invalid destination site.')})

    try:
        transfer_dt = timezone.make_aware(datetime.fromisoformat(transfer_date))
    except (ValueError, TypeError):
        transfer_dt = timezone.now()

    devices = Device.objects.filter(
        pk__in=device_ids,
        in_transfer=False,
        deleted_date__isnull=True,
        site__in=allowed,
    ).exclude(site=to_site)

    if not devices.exists():
        return JsonResponse({'success': False, 'message': _('No valid devices selected.')})

    created = 0
    for device in devices:
        DeviceTransfer.objects.create(
            device=device,
            from_site=device.site,
            to_site=to_site,
            transfer_date=transfer_dt,
            notes=notes,
            transferred_by=request.user,
            status=TransferStatus.PENDING,
        )
        device.in_transfer = True
        device.save(update_fields=['in_transfer'])
        created += 1

    return JsonResponse({'success': True,
                         'message': _(f'{created} transfer(s) created successfully.')})


@login_required
@require_http_methods(['POST'])
def device_transfer_accept(request, pk):
    if not has_permission(request.user, Perms.TRANSFERS_APPROVE):
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)

    from django.utils import timezone
    allowed = request.user.get_allowed_sites()
    allowed_ids = set(allowed.values_list('id', flat=True))

    t = get_object_or_404(DeviceTransfer, pk=pk)
    if t.status != TransferStatus.PENDING:
        return JsonResponse({'success': False, 'message': _('Transfer is not pending.')})
    if not _is_all_sites(request.user) and t.to_site_id not in allowed_ids:
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)

    t.status = TransferStatus.ACCEPTED
    t.resolved_by   = request.user
    t.resolved_date = timezone.now()
    t.save()
    t.device.site       = t.to_site
    t.device.in_transfer = False
    t.device.save(update_fields=['site', 'in_transfer'])
    return JsonResponse({'success': True, 'message': _('Transfer accepted. Device moved to new site.')})


@login_required
@require_http_methods(['POST'])
def device_transfer_reject(request, pk):
    if not has_permission(request.user, Perms.TRANSFERS_APPROVE):
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)

    from django.utils import timezone
    allowed = request.user.get_allowed_sites()
    allowed_ids = set(allowed.values_list('id', flat=True))

    t = get_object_or_404(DeviceTransfer, pk=pk)
    if t.status != TransferStatus.PENDING:
        return JsonResponse({'success': False, 'message': _('Transfer is not pending.')})
    if not _is_all_sites(request.user) and t.to_site_id not in allowed_ids:
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)

    t.status = TransferStatus.REJECTED
    t.resolved_by   = request.user
    t.resolved_date = timezone.now()
    t.save()
    t.device.in_transfer = False
    t.device.save(update_fields=['in_transfer'])
    return JsonResponse({'success': True, 'message': _('Transfer rejected. Device stays at original site.')})


@login_required
@require_http_methods(['POST'])
def device_transfer_delete(request, pk):
    if not has_permission(request.user, Perms.TRANSFERS_DELETE):
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)

    allowed = request.user.get_allowed_sites()
    allowed_ids = set(allowed.values_list('id', flat=True))

    t = get_object_or_404(DeviceTransfer, pk=pk)
    if t.status != TransferStatus.PENDING:
        return JsonResponse({'success': False, 'message': _('Only pending transfers can be cancelled.')})
    if not _is_all_sites(request.user) and t.from_site_id not in allowed_ids:
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)

    t.device.in_transfer = False
    t.device.save(update_fields=['in_transfer'])
    t.delete()
    return JsonResponse({'success': True, 'message': _('Transfer cancelled.')})


# ── Available devices/accessories for transfer modal ─────────────────────────

@login_required
def transfer_available_devices(request):
    if not has_permission(request.user, Perms.TRANSFERS_CREATE):
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)

    site_id = request.GET.get('site', '').strip()
    allowed = request.user.get_allowed_sites()

    qs = Device.objects.filter(
        deleted_date__isnull=True,
        in_transfer=False,
        site__in=allowed,
    ).select_related('category', 'brand', 'device_model')

    if site_id:
        qs = qs.filter(site_id=site_id)

    items = [
        {'id': d.pk,
         'text': f'{d.serial_number} — {d.device_model} ({d.category})',
         'serial': d.serial_number,
         'model': d.device_model.name,
         'category': d.category.name,
         'brand': d.brand.name,
         'site_id': d.site_id}
        for d in qs.order_by('serial_number')[:200]
    ]
    return JsonResponse({'success': True, 'items': items})


@login_required
def transfer_available_accessories(request):
    if not has_permission(request.user, Perms.TRANSFERS_CREATE):
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)

    site_id = request.GET.get('site', '').strip()
    allowed = request.user.get_allowed_sites()

    qs = Accessory.objects.filter(
        deleted_date__isnull=True,
        in_transfer=False,
        site__in=allowed,
    ).select_related('accessory_type', 'brand')

    if site_id:
        qs = qs.filter(site_id=site_id)

    items = [
        {'id': a.pk,
         'text': f'{a.accessory_type.name} — {a.serial_number or "No S/N"} ({a.brand.name if a.brand else "—"})',
         'serial': a.serial_number or '',
         'type': a.accessory_type.name,
         'brand': a.brand.name if a.brand else '',
         'site_id': a.site_id}
        for a in qs.order_by('accessory_type__name')[:200]
    ]
    return JsonResponse({'success': True, 'items': items})


# ── Accessory transfer list & detail ─────────────────────────────────────────

@login_required
@permission_required(Perms.TRANSFERS_VIEW)
def accessory_transfers_data(request):
    search   = request.GET.get('search', '').strip()
    status_f = request.GET.get('status', '').strip()
    allowed  = request.user.get_allowed_sites()
    allowed_ids = set(allowed.values_list('id', flat=True))
    all_sites   = _is_all_sites(request.user)

    qs = AccessoryTransfer.objects.filter(
        Q(from_site__in=allowed) | Q(to_site__in=allowed)
    ).select_related('accessory', 'accessory__accessory_type', 'from_site', 'to_site',
                     'transferred_by', 'resolved_by')

    if search:
        qs = qs.filter(
            Q(accessory__serial_number__icontains=search) |
            Q(accessory__accessory_type__name__icontains=search) |
            Q(from_site__name__icontains=search) |
            Q(to_site__name__icontains=search)
        )
    if status_f in (TransferStatus.PENDING, TransferStatus.ACCEPTED, TransferStatus.REJECTED):
        qs = qs.filter(status=status_f)

    qs = qs.order_by('-transfer_date')
    paginator = Paginator(qs, PAGE_SIZE)
    try:
        page_num = int(request.GET.get('page', 1))
    except (ValueError, TypeError):
        page_num = 1
    page_obj = paginator.get_page(page_num)

    items = []
    for t in page_obj:
        is_pending = t.status == TransferStatus.PENDING
        can_ar = is_pending and (all_sites or t.to_site_id in allowed_ids)
        can_del = is_pending and (all_sites or t.from_site_id in allowed_ids)
        items.append({
            'id': t.pk,
            'accessory_id': t.accessory_id,
            'accessory_type': t.accessory.accessory_type.name,
            'accessory_serial': t.accessory.serial_number or '',
            'from_site_name': t.from_site.name,
            'to_site_name': t.to_site.name,
            'transfer_date': t.transfer_date.strftime('%Y-%m-%d'),
            'status': t.status,
            'notes': t.notes or '',
            'transferred_by': t.transferred_by.full_name,
            'resolved_by': t.resolved_by.full_name if t.resolved_by else '',
            'resolved_date': t.resolved_date.strftime('%Y-%m-%d') if t.resolved_date else '',
            'can_accept': can_ar,
            'can_reject': can_ar,
            'can_delete': can_del,
        })
    return JsonResponse({'success': True, 'items': items, 'total': paginator.count,
                         'page': page_obj.number, 'num_pages': paginator.num_pages})


@login_required
def accessory_transfer_detail(request, pk):
    if not has_permission(request.user, Perms.TRANSFERS_VIEW):
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)
    allowed = request.user.get_allowed_sites()
    t = get_object_or_404(
        AccessoryTransfer.objects.filter(
            Q(from_site__in=allowed) | Q(to_site__in=allowed),
        ).select_related('accessory', 'accessory__accessory_type', 'from_site', 'to_site',
                         'transferred_by', 'resolved_by'),
        pk=pk,
    )
    return JsonResponse({'success': True, 'item': {
        'id': t.pk,
        'accessory_type': t.accessory.accessory_type.name,
        'accessory_serial': t.accessory.serial_number or '',
        'from_site_name': t.from_site.name,
        'to_site_name': t.to_site.name,
        'transfer_date': t.transfer_date.strftime('%Y-%m-%d %I:%M %p'),
        'status': t.status,
        'notes': t.notes or '',
        'transferred_by': t.transferred_by.full_name,
        'resolved_by': t.resolved_by.full_name if t.resolved_by else '',
        'resolved_date': t.resolved_date.strftime('%Y-%m-%d %I:%M %p') if t.resolved_date else '',
        'created_date': t.created_date.strftime('%Y-%m-%d %I:%M %p'),
    }})


# ── Accessory transfer create / accept / reject / delete ─────────────────────

@login_required
@require_http_methods(['POST'])
def accessory_transfer_create(request):
    if not has_permission(request.user, Perms.TRANSFERS_CREATE):
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)

    from django.utils import timezone
    from datetime import datetime

    allowed     = request.user.get_allowed_sites()

    accessory_ids = request.POST.getlist('accessory_ids[]')
    to_site_id    = request.POST.get('to_site', '').strip()
    transfer_date = request.POST.get('transfer_date', '').strip()
    notes         = request.POST.get('notes', '').strip() or None

    if not accessory_ids:
        return JsonResponse({'success': False, 'message': _('Select at least one accessory.')})
    if not to_site_id:
        return JsonResponse({'success': False, 'message': _('Select a destination site.')})

    try:
        to_site = Site.objects.get(pk=to_site_id)
    except Site.DoesNotExist:
        return JsonResponse({'success': False, 'message': _('Invalid destination site.')})

    try:
        transfer_dt = timezone.make_aware(datetime.fromisoformat(transfer_date))
    except (ValueError, TypeError):
        transfer_dt = timezone.now()

    accessories = Accessory.objects.filter(
        pk__in=accessory_ids,
        in_transfer=False,
        deleted_date__isnull=True,
        site__in=allowed,
    ).exclude(site=to_site)

    if not accessories.exists():
        return JsonResponse({'success': False, 'message': _('No valid accessories selected.')})

    created = 0
    for accessory in accessories:
        AccessoryTransfer.objects.create(
            accessory=accessory,
            from_site=accessory.site,
            to_site=to_site,
            transfer_date=transfer_dt,
            notes=notes,
            transferred_by=request.user,
            status=TransferStatus.PENDING,
        )
        accessory.in_transfer = True
        accessory.save(update_fields=['in_transfer'])
        created += 1

    return JsonResponse({'success': True,
                         'message': _(f'{created} transfer(s) created successfully.')})


@login_required
@require_http_methods(['POST'])
def accessory_transfer_accept(request, pk):
    if not has_permission(request.user, Perms.TRANSFERS_APPROVE):
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)

    from django.utils import timezone
    allowed_ids = set(request.user.get_allowed_sites().values_list('id', flat=True))

    t = get_object_or_404(AccessoryTransfer, pk=pk)
    if t.status != TransferStatus.PENDING:
        return JsonResponse({'success': False, 'message': _('Transfer is not pending.')})
    if not _is_all_sites(request.user) and t.to_site_id not in allowed_ids:
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)

    t.status = TransferStatus.ACCEPTED
    t.resolved_by   = request.user
    t.resolved_date = timezone.now()
    t.save()
    t.accessory.site       = t.to_site
    t.accessory.in_transfer = False
    t.accessory.save(update_fields=['site', 'in_transfer'])
    return JsonResponse({'success': True, 'message': _('Transfer accepted. Accessory moved to new site.')})


@login_required
@require_http_methods(['POST'])
def accessory_transfer_reject(request, pk):
    if not has_permission(request.user, Perms.TRANSFERS_APPROVE):
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)

    from django.utils import timezone
    allowed_ids = set(request.user.get_allowed_sites().values_list('id', flat=True))

    t = get_object_or_404(AccessoryTransfer, pk=pk)
    if t.status != TransferStatus.PENDING:
        return JsonResponse({'success': False, 'message': _('Transfer is not pending.')})
    if not _is_all_sites(request.user) and t.to_site_id not in allowed_ids:
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)

    t.status = TransferStatus.REJECTED
    t.resolved_by   = request.user
    t.resolved_date = timezone.now()
    t.save()
    t.accessory.in_transfer = False
    t.accessory.save(update_fields=['in_transfer'])
    return JsonResponse({'success': True, 'message': _('Transfer rejected. Accessory stays at original site.')})


@login_required
@require_http_methods(['POST'])
def accessory_transfer_delete(request, pk):
    if not has_permission(request.user, Perms.TRANSFERS_DELETE):
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)

    allowed_ids = set(request.user.get_allowed_sites().values_list('id', flat=True))

    t = get_object_or_404(AccessoryTransfer, pk=pk)
    if t.status != TransferStatus.PENDING:
        return JsonResponse({'success': False, 'message': _('Only pending transfers can be cancelled.')})
    if not _is_all_sites(request.user) and t.from_site_id not in allowed_ids:
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)

    t.accessory.in_transfer = False
    t.accessory.save(update_fields=['in_transfer'])
    t.delete()
    return JsonResponse({'success': True, 'message': _('Transfer cancelled.')})
