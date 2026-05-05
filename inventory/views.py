from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db.models import Q, Exists, OuterRef

PAGE_SIZE = 10

from accounts.permissions import permission_required, has_permission, Perms
from locations.models import Site
from .models import (Brand, DeviceCategory, DeviceModel, CPU, GPU,
                     OperatingSystem, DeviceFlag, AccessoryType, Device, Accessory)
from .forms import (BrandForm, DeviceCategoryForm, DeviceModelForm, CPUForm, GPUForm,
                    OperatingSystemForm, AccessoryTypeForm,
                    DeviceForm, ChangeFlagForm, AccessoryForm)

# System-managed flags that must only change through their dedicated flows
_SYSTEM_FLAGS = {DeviceFlag.ASSIGNED, DeviceFlag.UNDER_MAINTENANCE}
# Flags a user may freely set through the "change flag" action
_FREE_FLAGS = {DeviceFlag.AVAILABLE, DeviceFlag.LOST, DeviceFlag.RETIRED}


# ── Lookup registry ───────────────────────────────────────────────────────────

def _serialize_base(obj):
    return {'id': obj.pk, 'name': obj.name,
            'created_date': obj.created_date.strftime('%Y-%m-%d')}


def _serialize_with_brand(obj):
    d = _serialize_base(obj)
    d['brand_id']   = obj.brand_id
    d['brand_name'] = obj.brand.name
    return d


def _serialize_device_model(obj):
    d = _serialize_with_brand(obj)
    d['category_id']   = obj.category_id
    d['category_name'] = obj.category.name
    return d


LOOKUP_REGISTRY = {
    'brands':          (Brand,           BrandForm,           'name',          _serialize_base),
    'categories':      (DeviceCategory,  DeviceCategoryForm,  'name',          _serialize_base),
    'models':          (DeviceModel,     DeviceModelForm,     'name,brand,category', _serialize_device_model),
    'cpus':            (CPU,             CPUForm,             'name,brand',    _serialize_with_brand),
    'gpus':            (GPU,             GPUForm,             'name,brand',    _serialize_with_brand),
    'os':              (OperatingSystem, OperatingSystemForm, 'name',          _serialize_base),
    'accessory-types': (AccessoryType,   AccessoryTypeForm,   'name',          _serialize_base),
}


def _get_lookup(lookup_type):
    cfg = LOOKUP_REGISTRY.get(lookup_type)
    if not cfg:
        from django.http import Http404
        raise Http404
    return cfg   # (model, form_cls, field_names_str, serialize_fn)


# ── Lookup views ──────────────────────────────────────────────────────────────

@login_required
@permission_required(Perms.LOOKUPS_VIEW)
def lookups_index(request):
    return render(request, 'inventory/lookups.html')


@login_required
@permission_required(Perms.LOOKUPS_VIEW)
def lookup_data(request, lookup_type):
    model, _, _, serialize = _get_lookup(lookup_type)
    search = request.GET.get('search', '').strip()
    qs = model.objects.filter(deleted_date__isnull=True)
    if lookup_type in ('models', 'cpus', 'gpus'):
        qs = qs.select_related('brand')
    if lookup_type == 'models':
        qs = qs.select_related('category')
    if search:
        qs = qs.filter(name__icontains=search)
    qs = qs.order_by('name')
    paginator = Paginator(qs, PAGE_SIZE)
    try:
        page_num = int(request.GET.get('page', 1))
    except (ValueError, TypeError):
        page_num = 1
    page_obj  = paginator.get_page(page_num)
    items = [serialize(obj) for obj in page_obj]
    return JsonResponse({'success': True, 'items': items, 'total': paginator.count,
                         'page': page_obj.number, 'num_pages': paginator.num_pages})


@login_required
def lookup_item_detail(request, lookup_type, pk):
    if not has_permission(request.user, Perms.LOOKUPS_VIEW):
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)
    model, _, _, serialize = _get_lookup(lookup_type)
    obj = get_object_or_404(model.objects.select_related('created_by', 'updated_by'), pk=pk, deleted_date__isnull=True)
    item = serialize(obj)
    item.update({
        'created_by': obj.created_by.full_name if obj.created_by else '',
        'created_date': obj.created_date.strftime('%Y-%m-%d %I:%M %p'),
        'updated_by': obj.updated_by.full_name if obj.updated_by else '',
        'updated_date': obj.updated_date.strftime('%Y-%m-%d %I:%M %p') if obj.updated_date else '',
    })
    return JsonResponse({'success': True, 'item': item})


@login_required
@require_http_methods(['POST'])
def lookup_create(request, lookup_type):
    if not has_permission(request.user, Perms.LOOKUPS_CREATE):
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)
    model, form_cls, __, __ = _get_lookup(lookup_type)
    form = form_cls(request.POST)
    if form.is_valid():
        obj = form.save(commit=False)
        obj.created_by = request.user
        obj.save()
        return JsonResponse({'success': True, 'message': _('Item created successfully.')})
    errors = {f: [str(e) for e in v] for f, v in form.errors.items()}
    return JsonResponse({'success': False, 'errors': errors})


@login_required
@require_http_methods(['POST'])
def lookup_edit(request, lookup_type, pk):
    if not has_permission(request.user, Perms.LOOKUPS_EDIT):
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)
    model, form_cls, __, __ = _get_lookup(lookup_type)
    obj = get_object_or_404(model, pk=pk, deleted_date__isnull=True)
    form = form_cls(request.POST, instance=obj)
    if form.is_valid():
        item = form.save(commit=False)
        item.updated_by = request.user
        item.save()
        return JsonResponse({'success': True, 'message': _('Item updated successfully.')})
    errors = {f: [str(e) for e in v] for f, v in form.errors.items()}
    return JsonResponse({'success': False, 'errors': errors})


@login_required
@require_http_methods(['POST'])
def lookup_delete(request, lookup_type, pk):
    if not has_permission(request.user, Perms.LOOKUPS_DELETE):
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)
    model, __, __, __ = _get_lookup(lookup_type)
    obj = get_object_or_404(model, pk=pk, deleted_date__isnull=True)
    # Block deletion if referenced by other records
    related_checks = {
        'brands':          [('devices', True), ('accessories', True), ('device_models', True), ('cpus', True), ('gpus', True)],
        'categories':      [('devices', True), ('device_models', True)],
        'models':          [('devices', True)],
        'cpus':            [('devices', True)],
        'gpus':            [('devices', True)],
        'os':              [('devices', True)],
        'accessory-types': [('accessories', True)],
    }
    for rel_name, use_soft_delete_filter in related_checks.get(lookup_type, []):
        qs = getattr(obj, rel_name)
        if use_soft_delete_filter:
            qs = qs.filter(deleted_date__isnull=True)
        if qs.exists():
            return JsonResponse({'success': False, 'message': _('Cannot delete: item is used by existing records.')})
    obj.deleted_date = timezone.now()
    obj.save()
    return JsonResponse({'success': True, 'message': _('Item deleted successfully.')})


# ── Devices ───────────────────────────────────────────────────────────────────

@login_required
@permission_required(Perms.DEVICES_VIEW)
def devices_index(request):
    show_specs = has_permission(request.user, Perms.DEVICES_VIEW_SPECS)
    # Only free flags for create/edit modals — assigned/under_maintenance are system-managed
    create_edit_flag_choices = [(v, l) for v, l in DeviceFlag.choices if v in _FREE_FLAGS]
    from maintenance.models import MaintenanceRecord
    return render(request, 'inventory/devices.html', {
        'sites':      request.user.get_allowed_sites().filter(deleted_date__isnull=True).order_by('name'),
        'categories': DeviceCategory.objects.filter(deleted_date__isnull=True).order_by('name'),
        'brands':     Brand.objects.filter(deleted_date__isnull=True).order_by('name'),
        'models':     DeviceModel.objects.filter(deleted_date__isnull=True).select_related('brand').order_by('name'),
        'flag_choices': DeviceFlag.choices,
        'create_edit_flag_choices': create_edit_flag_choices,
        'type_choices': MaintenanceRecord.MaintenanceType.choices,
        'cpus':       CPU.objects.filter(deleted_date__isnull=True).order_by('name'),
        'gpus':       GPU.objects.filter(deleted_date__isnull=True).order_by('name'),
        'os_list':    OperatingSystem.objects.filter(deleted_date__isnull=True).order_by('name'),
        'show_specs': show_specs,
    })


@login_required
@permission_required(Perms.DEVICES_VIEW)
def devices_data(request):
    search   = request.GET.get('search', '').strip()
    cat_id   = request.GET.get('category', '').strip()
    site_id  = request.GET.get('site', '').strip()
    flag_id  = request.GET.get('flag', '').strip()
    show_specs = has_permission(request.user, Perms.DEVICES_VIEW_SPECS)

    from assignments.models import DeviceAssignment
    qs = Device.objects.filter(
        deleted_date__isnull=True,
        site__in=request.user.get_allowed_sites(),
    ).select_related('category', 'brand', 'device_model', 'site').annotate(
        has_active_assignment=Exists(
            DeviceAssignment.objects.filter(device=OuterRef('pk'), returned_date__isnull=True)
        )
    )
    if search:
        qs = qs.filter(
            Q(serial_number__icontains=search) |
            Q(brand__name__icontains=search) |
            Q(device_model__name__icontains=search)
        )
    if cat_id:  qs = qs.filter(category_id=cat_id)
    if site_id: qs = qs.filter(site_id=site_id)
    if flag_id: qs = qs.filter(flag=flag_id)

    qs = qs.order_by('-created_date')
    paginator = Paginator(qs, PAGE_SIZE)
    try:
        page_num = int(request.GET.get('page', 1))
    except (ValueError, TypeError):
        page_num = 1
    page_obj  = paginator.get_page(page_num)
    items = []
    for d in page_obj:
        item = {
            'id': d.pk,
            'serial_number': d.serial_number,
            'category_id': d.category_id, 'category_name': d.category.name,
            'brand_id': d.brand_id, 'brand_name': d.brand.name,
            'model_id': d.device_model_id, 'model_name': d.device_model.name,
            'site_id': d.site_id, 'site_name': d.site.name,
            'flag': d.flag, 'flag_name': d.get_flag_display(),
            'maintenance_mode': d.maintenance_mode,
            'has_active_assignment': d.has_active_assignment,
            'created_date': d.created_date.strftime('%Y-%m-%d'),
        }
        if show_specs:
            item.update({
                'cpu_id': d.cpu_id or '', 'gpu_id': d.gpu_id or '',
                'ram_size_gb': d.ram_size_gb or '', 'hdd_storage_gb': d.hdd_storage_gb or '',
                'ssd_storage_gb': d.ssd_storage_gb or '',
                'os_id': d.operating_system_id or '',
                'screen_size_inch': d.screen_size_inch or '',
                'ports_number': d.ports_number or '',
            })
        items.append(item)
    return JsonResponse({'success': True, 'items': items, 'total': paginator.count,
                         'page': page_obj.number, 'num_pages': paginator.num_pages})


@login_required
def device_detail(request, pk):
    if not has_permission(request.user, Perms.DEVICES_VIEW):
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)
    d = get_object_or_404(
        Device.objects.filter(
            site__in=request.user.get_allowed_sites(),
        ).select_related('category', 'brand', 'device_model', 'site',
                         'cpu', 'gpu', 'operating_system', 'created_by', 'updated_by'),
        pk=pk, deleted_date__isnull=True,
    )
    show_specs = has_permission(request.user, Perms.DEVICES_VIEW_SPECS)
    item = {
        'id': d.pk, 'serial_number': d.serial_number,
        'category_id': d.category_id,     'category_name': d.category.name,
        'brand_id': d.brand_id,           'brand_name': d.brand.name,
        'device_model_id': d.device_model_id, 'model_name': d.device_model.name,
        'site_id': d.site_id,             'site_name': d.site.name,
        'flag': d.flag, 'flag_name': d.get_flag_display(),
        'notes': d.notes or '',
        'created_by': d.created_by.full_name,
        'created_date': d.created_date.strftime('%Y-%m-%d %I:%M %p'),
        'updated_by': d.updated_by.full_name if d.updated_by else '',
        'updated_date': d.updated_date.strftime('%Y-%m-%d %I:%M %p') if d.updated_date else '',
    }
    if show_specs:
        item.update({
            'cpu_id': d.cpu_id or '',   'cpu_name': d.cpu.name if d.cpu else '',
            'gpu_id': d.gpu_id or '',   'gpu_name': d.gpu.name if d.gpu else '',
            'ram_size_gb': d.ram_size_gb or '',
            'hdd_storage_gb': d.hdd_storage_gb or '',
            'ssd_storage_gb': d.ssd_storage_gb or '',
            'operating_system_id': d.operating_system_id or '',
            'os_name': d.operating_system.name if d.operating_system else '',
            'screen_size_inch': d.screen_size_inch or '',
            'ports_number': d.ports_number or '',
        })
    return JsonResponse({'success': True, 'item': item})


@login_required
@require_http_methods(['POST'])
def device_create(request):
    if not has_permission(request.user, Perms.DEVICES_CREATE):
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)
    form = DeviceForm(request.POST)
    if form.is_valid():
        obj = form.save(commit=False)
        obj.created_by = request.user
        obj.save()
        return JsonResponse({'success': True, 'message': _('Device created successfully.')})
    errors = {f: [str(e) for e in v] for f, v in form.errors.items()}
    return JsonResponse({'success': False, 'errors': errors})


@login_required
@require_http_methods(['POST'])
def device_edit(request, pk):
    if not has_permission(request.user, Perms.DEVICES_EDIT):
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)
    device = get_object_or_404(Device, pk=pk, deleted_date__isnull=True)
    form = DeviceForm(request.POST, instance=device)
    if form.is_valid():
        obj = form.save(commit=False)
        # Preserve system-managed flags — they are only changed through assignment/maintenance flows
        if device.flag in _SYSTEM_FLAGS:
            obj.flag = device.flag
        obj.updated_by = request.user
        obj.save()
        return JsonResponse({'success': True, 'message': _('Device updated successfully.')})
    errors = {f: [str(e) for e in v] for f, v in form.errors.items()}
    return JsonResponse({'success': False, 'errors': errors})


@login_required
@require_http_methods(['POST'])
def device_delete(request, pk):
    if not has_permission(request.user, Perms.DEVICES_DELETE):
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)
    device = get_object_or_404(Device, pk=pk, deleted_date__isnull=True)
    if device.assignments.exists():
        return JsonResponse({'success': False, 'message': _('Cannot delete device: it has assignment records.')})
    if device.transfers.exists():
        return JsonResponse({'success': False, 'message': _('Cannot delete device: it has transfer records.')})
    if device.maintenance_records.exists():
        return JsonResponse({'success': False, 'message': _('Cannot delete device: it has maintenance records.')})
    if device.accessories.exists():
        return JsonResponse({'success': False, 'message': _('Cannot delete device: it has linked accessories.')})
    device.deleted_date = timezone.now()
    device.save()
    return JsonResponse({'success': True, 'message': _('Device deleted successfully.')})


@login_required
@require_http_methods(['POST'])
def device_retire(request, pk):
    if not has_permission(request.user, Perms.DEVICES_RETIRE):
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)
    device = get_object_or_404(Device, pk=pk, deleted_date__isnull=True)
    device.flag = DeviceFlag.RETIRED
    device.save()
    return JsonResponse({'success': True, 'message': _('Device retired successfully.')})


@login_required
@require_http_methods(['POST'])
def device_change_flag(request, pk):
    if not has_permission(request.user, Perms.DEVICES_CHANGE_FLAG):
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)
    device = get_object_or_404(Device, pk=pk, deleted_date__isnull=True)
    # Block all flag changes while under maintenance
    if device.flag == DeviceFlag.UNDER_MAINTENANCE:
        return JsonResponse({'success': False,
                             'message': _('Device is under active maintenance. Close the maintenance record first.')})
    form = ChangeFlagForm(request.POST)
    if form.is_valid():
        new_flag = form.cleaned_data['flag']
        # System-managed flags must go through their dedicated flows
        if new_flag == DeviceFlag.UNDER_MAINTENANCE:
            return JsonResponse({'success': False,
                                 'message': _('Use the Maintenance page to put a device under maintenance.')})
        if new_flag == DeviceFlag.ASSIGNED:
            return JsonResponse({'success': False,
                                 'message': _('Use the Assignments page to assign a device to an employee.')})
        # Block clearing an active assignment without returning it
        if device.assignments.filter(returned_date__isnull=True).exists():
            return JsonResponse({'success': False,
                                 'message': _('Device is currently assigned to an employee. Return it first.')})
        device.flag = new_flag
        device.save()
        return JsonResponse({'success': True, 'message': _('Device flag updated.'),
                             'flag': device.flag, 'flag_name': device.get_flag_display()})
    errors = {f: [str(e) for e in v] for f, v in form.errors.items()}
    return JsonResponse({'success': False, 'errors': errors})


@login_required
@require_http_methods(['POST'])
def device_toggle_maintenance(request, pk):
    if not has_permission(request.user, Perms.DEVICES_TOGGLE_MAINTENANCE):
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)
    device = get_object_or_404(Device, pk=pk, deleted_date__isnull=True)
    device.maintenance_mode = not device.maintenance_mode
    if device.maintenance_mode:
        device.flag = DeviceFlag.UNDER_MAINTENANCE
    else:
        # Restore to assigned if device still has an active assignment
        has_active = device.assignments.filter(returned_date__isnull=True).exists()
        device.flag = DeviceFlag.ASSIGNED if has_active else DeviceFlag.AVAILABLE
    device.save()
    return JsonResponse({
        'success': True,
        'maintenance_mode': device.maintenance_mode,
        'message': _('Maintenance mode enabled.') if device.maintenance_mode else _('Maintenance mode disabled.'),
    })


# ── Accessories ───────────────────────────────────────────────────────────────

@login_required
@permission_required(Perms.ACCESSORIES_VIEW)
def accessories_index(request):
    allowed = request.user.get_allowed_sites()
    create_edit_flag_choices = [(v, l) for v, l in DeviceFlag.choices if v in _FREE_FLAGS]
    from maintenance.models import MaintenanceRecord
    return render(request, 'inventory/accessories.html', {
        'types':        AccessoryType.objects.filter(deleted_date__isnull=True).order_by('name'),
        'brands':       Brand.objects.filter(deleted_date__isnull=True).order_by('name'),
        'sites':        allowed.filter(deleted_date__isnull=True).order_by('name'),
        'flag_choices': DeviceFlag.choices,
        'create_edit_flag_choices': create_edit_flag_choices,
        'type_choices': MaintenanceRecord.MaintenanceType.choices,
        'devices':      Device.objects.filter(deleted_date__isnull=True, site__in=allowed).order_by('serial_number'),
    })


@login_required
@permission_required(Perms.ACCESSORIES_VIEW)
def accessories_data(request):
    search  = request.GET.get('search', '').strip()
    type_id = request.GET.get('type', '').strip()
    site_id = request.GET.get('site', '').strip()
    flag_id = request.GET.get('flag', '').strip()
    from assignments.models import AccessoryAssignment
    qs = Accessory.objects.filter(
        deleted_date__isnull=True,
        site__in=request.user.get_allowed_sites(),
    ).select_related('accessory_type', 'brand', 'site').annotate(
        has_active_assignment=Exists(
            AccessoryAssignment.objects.filter(accessory=OuterRef('pk'), returned_date__isnull=True)
        )
    )
    if search:
        qs = qs.filter(
            Q(serial_number__icontains=search) |
            Q(accessory_type__name__icontains=search)
        )
    if type_id: qs = qs.filter(accessory_type_id=type_id)
    if site_id: qs = qs.filter(site_id=site_id)
    if flag_id: qs = qs.filter(flag=flag_id)
    qs = qs.order_by('-created_date')
    paginator = Paginator(qs, PAGE_SIZE)
    try:
        page_num = int(request.GET.get('page', 1))
    except (ValueError, TypeError):
        page_num = 1
    page_obj  = paginator.get_page(page_num)
    items = [
        {'id': a.pk,
         'type_id': a.accessory_type_id, 'type_name': a.accessory_type.name,
         'serial_number': a.serial_number or '',
         'brand_id': a.brand_id or '', 'brand_name': a.brand.name if a.brand else '',
         'site_id': a.site_id, 'site_name': a.site.name,
         'flag': a.flag, 'flag_name': a.get_flag_display(),
         'has_active_assignment': a.has_active_assignment,
         'created_date': a.created_date.strftime('%Y-%m-%d')}
        for a in page_obj
    ]
    return JsonResponse({'success': True, 'items': items, 'total': paginator.count,
                         'page': page_obj.number, 'num_pages': paginator.num_pages})


@login_required
def accessory_detail(request, pk):
    if not has_permission(request.user, Perms.ACCESSORIES_VIEW):
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)
    a = get_object_or_404(
        Accessory.objects.filter(
            site__in=request.user.get_allowed_sites(),
        ).select_related('accessory_type', 'brand', 'site', 'created_by', 'updated_by'),
        pk=pk, deleted_date__isnull=True,
    )
    return JsonResponse({'success': True, 'item': {
        'id': a.pk,
        'accessory_type_id': a.accessory_type_id, 'type_name': a.accessory_type.name,
        'serial_number': a.serial_number or '',
        'brand_id': a.brand_id or '', 'brand_name': a.brand.name if a.brand else '',
        'site_id': a.site_id,         'site_name': a.site.name,
        'flag': a.flag, 'flag_name': a.get_flag_display(),
        'notes': a.notes or '',
        'created_by': a.created_by.full_name,
        'created_date': a.created_date.strftime('%Y-%m-%d %I:%M %p'),
        'updated_by': a.updated_by.full_name if a.updated_by else '',
        'updated_date': a.updated_date.strftime('%Y-%m-%d %I:%M %p') if a.updated_date else '',
    }})


@login_required
@require_http_methods(['POST'])
def accessory_create(request):
    if not has_permission(request.user, Perms.ACCESSORIES_CREATE):
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)
    form = AccessoryForm(request.POST)
    if form.is_valid():
        obj = form.save(commit=False)
        obj.created_by = request.user
        obj.save()
        return JsonResponse({'success': True, 'message': _('Accessory created successfully.')})
    errors = {f: [str(e) for e in v] for f, v in form.errors.items()}
    return JsonResponse({'success': False, 'errors': errors})


@login_required
@require_http_methods(['POST'])
def accessory_edit(request, pk):
    if not has_permission(request.user, Perms.ACCESSORIES_EDIT):
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)
    a = get_object_or_404(Accessory, pk=pk, deleted_date__isnull=True)
    form = AccessoryForm(request.POST, instance=a)
    if form.is_valid():
        obj = form.save(commit=False)
        # Preserve system-managed flags
        if a.flag in _SYSTEM_FLAGS:
            obj.flag = a.flag
        obj.updated_by = request.user
        obj.save()
        return JsonResponse({'success': True, 'message': _('Accessory updated successfully.')})
    errors = {f: [str(e) for e in v] for f, v in form.errors.items()}
    return JsonResponse({'success': False, 'errors': errors})


@login_required
@require_http_methods(['POST'])
def accessory_change_flag(request, pk):
    if not has_permission(request.user, Perms.ACCESSORIES_EDIT):
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)
    a = get_object_or_404(Accessory, pk=pk, deleted_date__isnull=True)
    # Block all flag changes while under maintenance
    if a.flag == DeviceFlag.UNDER_MAINTENANCE:
        return JsonResponse({'success': False,
                             'message': _('Accessory is under active maintenance. Close the maintenance record first.')})
    form = ChangeFlagForm(request.POST)
    if form.is_valid():
        new_flag = form.cleaned_data['flag']
        if new_flag == DeviceFlag.UNDER_MAINTENANCE:
            return JsonResponse({'success': False,
                                 'message': _('Use the Maintenance page to put an accessory under maintenance.')})
        if new_flag == DeviceFlag.ASSIGNED:
            return JsonResponse({'success': False,
                                 'message': _('Use the Assignments page to assign an accessory to an employee.')})
        if a.accessory_assignments.filter(returned_date__isnull=True).exists():
            return JsonResponse({'success': False,
                                 'message': _('Accessory is currently assigned to an employee. Return it first.')})
        a.flag = new_flag
        a.save()
        return JsonResponse({'success': True, 'message': _('Accessory flag updated.'),
                             'flag': a.flag, 'flag_name': a.get_flag_display()})
    errors = {f: [str(e) for e in v] for f, v in form.errors.items()}
    return JsonResponse({'success': False, 'errors': errors})


@login_required
@require_http_methods(['POST'])
def accessory_delete(request, pk):
    if not has_permission(request.user, Perms.ACCESSORIES_DELETE):
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)
    a = get_object_or_404(Accessory, pk=pk, deleted_date__isnull=True)
    a.deleted_date = timezone.now()
    a.save()
    return JsonResponse({'success': True, 'message': _('Accessory deleted successfully.')})
