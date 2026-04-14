from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db.models import Q

from accounts.permissions import permission_required, has_permission, Perms
from locations.models import Site
from .models import (Brand, DeviceCategory, DeviceModel, CPU, GPU,
                     OperatingSystem, Flag, AccessoryType, Device, Accessory)
from .forms import (BrandForm, DeviceCategoryForm, DeviceModelForm, CPUForm, GPUForm,
                    OperatingSystemForm, FlagForm, AccessoryTypeForm,
                    DeviceForm, ChangeFlagForm, AccessoryForm)


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
    'flags':           (Flag,            FlagForm,            'name',          _serialize_base),
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
    items = [serialize(obj) for obj in qs.order_by('name')]
    return JsonResponse({'success': True, 'items': items, 'total': len(items)})


@login_required
def lookup_item_detail(request, lookup_type, pk):
    if not has_permission(request.user, Perms.LOOKUPS_EDIT):
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)
    model, _, _, serialize = _get_lookup(lookup_type)
    obj = get_object_or_404(model, pk=pk, deleted_date__isnull=True)
    return JsonResponse({'success': True, 'item': serialize(obj)})


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
        form.save()
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
    obj.deleted_date = timezone.now()
    obj.save()
    return JsonResponse({'success': True, 'message': _('Item deleted successfully.')})


# ── Devices ───────────────────────────────────────────────────────────────────

@login_required
@permission_required(Perms.DEVICES_VIEW)
def devices_index(request):
    show_specs = has_permission(request.user, Perms.DEVICES_VIEW_SPECS)
    return render(request, 'inventory/devices.html', {
        'sites':      Site.objects.filter(deleted_date__isnull=True).order_by('name'),
        'categories': DeviceCategory.objects.filter(deleted_date__isnull=True).order_by('name'),
        'brands':     Brand.objects.filter(deleted_date__isnull=True).order_by('name'),
        'models':     DeviceModel.objects.filter(deleted_date__isnull=True).select_related('brand').order_by('name'),
        'flags':      Flag.objects.filter(deleted_date__isnull=True).order_by('name'),
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

    qs = Device.objects.filter(deleted_date__isnull=True).select_related(
        'category', 'brand', 'device_model', 'site', 'flag'
    )
    if search:
        qs = qs.filter(
            Q(serial_number__icontains=search) |
            Q(brand__name__icontains=search) |
            Q(device_model__name__icontains=search)
        )
    if cat_id:  qs = qs.filter(category_id=cat_id)
    if site_id: qs = qs.filter(site_id=site_id)
    if flag_id: qs = qs.filter(flag_id=flag_id)

    items = []
    for d in qs.order_by('-created_date'):
        item = {
            'id': d.pk,
            'serial_number': d.serial_number,
            'category_id': d.category_id, 'category_name': d.category.name,
            'brand_id': d.brand_id, 'brand_name': d.brand.name,
            'model_id': d.device_model_id, 'model_name': d.device_model.name,
            'site_id': d.site_id, 'site_name': d.site.name,
            'flag_id': d.flag_id, 'flag_name': d.flag.name,
            'maintenance_mode': d.maintenance_mode,
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
    return JsonResponse({'success': True, 'items': items, 'total': len(items)})


@login_required
def device_detail(request, pk):
    if not has_permission(request.user, Perms.DEVICES_EDIT):
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)
    d = get_object_or_404(
        Device.objects.select_related('category', 'brand', 'device_model', 'site', 'flag',
                                      'cpu', 'gpu', 'operating_system'),
        pk=pk, deleted_date__isnull=True,
    )
    show_specs = has_permission(request.user, Perms.DEVICES_VIEW_SPECS)
    item = {
        'id': d.pk, 'serial_number': d.serial_number,
        'category_id': d.category_id,     'category_name': d.category.name,
        'brand_id': d.brand_id,           'brand_name': d.brand.name,
        'device_model_id': d.device_model_id, 'model_name': d.device_model.name,
        'site_id': d.site_id,             'site_name': d.site.name,
        'flag_id': d.flag_id,             'flag_name': d.flag.name,
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
        form.save()
        return JsonResponse({'success': True, 'message': _('Device updated successfully.')})
    errors = {f: [str(e) for e in v] for f, v in form.errors.items()}
    return JsonResponse({'success': False, 'errors': errors})


@login_required
@require_http_methods(['POST'])
def device_delete(request, pk):
    if not has_permission(request.user, Perms.DEVICES_DELETE):
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)
    device = get_object_or_404(Device, pk=pk, deleted_date__isnull=True)
    device.deleted_date = timezone.now()
    device.save()
    return JsonResponse({'success': True, 'message': _('Device deleted successfully.')})


@login_required
@require_http_methods(['POST'])
def device_retire(request, pk):
    if not has_permission(request.user, Perms.DEVICES_RETIRE):
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)
    device = get_object_or_404(Device, pk=pk, deleted_date__isnull=True)
    retired_flag = Flag.objects.filter(name='Retired').first()
    if not retired_flag:
        return JsonResponse({'success': False, 'message': _('Retired flag not found.')})
    device.flag = retired_flag
    device.save()
    return JsonResponse({'success': True, 'message': _('Device retired successfully.')})


@login_required
@require_http_methods(['POST'])
def device_change_flag(request, pk):
    if not has_permission(request.user, Perms.DEVICES_CHANGE_FLAG):
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)
    device = get_object_or_404(Device, pk=pk, deleted_date__isnull=True)
    form = ChangeFlagForm(request.POST)
    if form.is_valid():
        device.flag = form.cleaned_data['flag']
        device.save()
        return JsonResponse({'success': True, 'message': _('Device flag updated.'),
                             'flag_name': device.flag.name})
    errors = {f: [str(e) for e in v] for f, v in form.errors.items()}
    return JsonResponse({'success': False, 'errors': errors})


@login_required
@require_http_methods(['POST'])
def device_toggle_maintenance(request, pk):
    if not has_permission(request.user, Perms.DEVICES_TOGGLE_MAINTENANCE):
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)
    device = get_object_or_404(Device, pk=pk, deleted_date__isnull=True)
    device.maintenance_mode = not device.maintenance_mode
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
    return render(request, 'inventory/accessories.html', {
        'types':   AccessoryType.objects.filter(deleted_date__isnull=True).order_by('name'),
        'brands':  Brand.objects.filter(deleted_date__isnull=True).order_by('name'),
        'sites':   Site.objects.filter(deleted_date__isnull=True).order_by('name'),
        'flags':   Flag.objects.filter(deleted_date__isnull=True).order_by('name'),
        'devices': Device.objects.filter(deleted_date__isnull=True).order_by('serial_number'),
    })


@login_required
@permission_required(Perms.ACCESSORIES_VIEW)
def accessories_data(request):
    search  = request.GET.get('search', '').strip()
    type_id = request.GET.get('type', '').strip()
    site_id = request.GET.get('site', '').strip()
    flag_id = request.GET.get('flag', '').strip()
    qs = Accessory.objects.filter(deleted_date__isnull=True).select_related(
        'accessory_type', 'brand', 'device', 'site', 'flag'
    )
    if search:
        qs = qs.filter(
            Q(serial_number__icontains=search) |
            Q(accessory_type__name__icontains=search)
        )
    if type_id: qs = qs.filter(accessory_type_id=type_id)
    if site_id: qs = qs.filter(site_id=site_id)
    if flag_id: qs = qs.filter(flag_id=flag_id)
    items = [
        {'id': a.pk,
         'type_id': a.accessory_type_id, 'type_name': a.accessory_type.name,
         'serial_number': a.serial_number or '',
         'brand_id': a.brand_id or '', 'brand_name': a.brand.name if a.brand else '',
         'device_id': a.device_id or '', 'device_serial': a.device.serial_number if a.device else '',
         'site_id': a.site_id, 'site_name': a.site.name,
         'flag_id': a.flag_id, 'flag_name': a.flag.name,
         'created_date': a.created_date.strftime('%Y-%m-%d')}
        for a in qs.order_by('-created_date')
    ]
    return JsonResponse({'success': True, 'items': items, 'total': len(items)})


@login_required
def accessory_detail(request, pk):
    if not has_permission(request.user, Perms.ACCESSORIES_EDIT):
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)
    a = get_object_or_404(
        Accessory.objects.select_related('accessory_type', 'brand', 'device', 'site', 'flag'),
        pk=pk, deleted_date__isnull=True,
    )
    return JsonResponse({'success': True, 'item': {
        'id': a.pk,
        'accessory_type_id': a.accessory_type_id, 'type_name': a.accessory_type.name,
        'serial_number': a.serial_number or '',
        'brand_id': a.brand_id or '',   'brand_name': a.brand.name if a.brand else '',
        'device_id': a.device_id or '', 'device_serial': a.device.serial_number if a.device else '',
        'site_id': a.site_id,           'site_name': a.site.name,
        'flag_id': a.flag_id,           'flag_name': a.flag.name,
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
        form.save()
        return JsonResponse({'success': True, 'message': _('Accessory updated successfully.')})
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
