"""
it_assets/select2_api.py
─────────────────────────
Single AJAX endpoint for all Select2 dropdowns.

URL:  /select2/<entity>/
Params:
    q       – search term
    page    – page number (default 1)
    brand   – filter device-models / cpus / gpus by brand id
    governorate – filter sites by governorate id
"""

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse

from inventory.models import (Brand, DeviceCategory, DeviceModel, CPU, GPU,
                               OperatingSystem, AccessoryType, Device)
from locations.models import Governorate, Site
from employees.models import Department, Employee

PAGE_SIZE = 25


@login_required
def select2_data(request, entity):
    q = request.GET.get('q', '').strip()
    try:
        page = max(1, int(request.GET.get('page', 1)))
    except (ValueError, TypeError):
        page = 1

    start = (page - 1) * PAGE_SIZE
    end   = start + PAGE_SIZE

    handlers = {
        'brands':          _brands,
        'categories':      _categories,
        'device-models':   _device_models,
        'cpus':            _cpus,
        'gpus':            _gpus,
        'os':              _os,
        'accessory-types': _accessory_types,
        'sites':           _sites,
        'governorates':    _governorates,
        'devices':         _devices,
        'employees':       _employees,
        'departments':     _departments,
    }

    handler = handlers.get(entity)
    if not handler:
        return JsonResponse({'results': [], 'pagination': {'more': False}})

    results, total = handler(q, start, end, request)
    return JsonResponse({'results': results, 'pagination': {'more': end < total}})


# ── Helpers ───────────────────────────────────────────────────────────────────

def _simple(qs, start, end):
    total = qs.count()
    items = [{'id': o.pk, 'text': o.name} for o in qs[start:end]]
    return items, total


def _brands(q, start, end, request):
    qs = Brand.objects.filter(deleted_date__isnull=True)
    if q: qs = qs.filter(name__icontains=q)
    return _simple(qs.order_by('name'), start, end)


def _categories(q, start, end, request):
    qs = DeviceCategory.objects.filter(deleted_date__isnull=True)
    if q: qs = qs.filter(name__icontains=q)
    return _simple(qs.order_by('name'), start, end)


def _device_models(q, start, end, request):
    qs = DeviceModel.objects.filter(deleted_date__isnull=True).select_related('brand', 'category')
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(brand__name__icontains=q))
    brand_id = request.GET.get('brand')
    if brand_id:
        qs = qs.filter(brand_id=brand_id)
    qs = qs.order_by('name')
    total = qs.count()
    items = [{'id': o.pk, 'text': f'{o.name} ({o.brand.name})'} for o in qs[start:end]]
    return items, total


def _cpus(q, start, end, request):
    qs = CPU.objects.filter(deleted_date__isnull=True).select_related('brand')
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(brand__name__icontains=q))
    qs = qs.order_by('name')
    total = qs.count()
    items = [{'id': o.pk, 'text': f'{o.name} ({o.brand.name})'} for o in qs[start:end]]
    return items, total


def _gpus(q, start, end, request):
    qs = GPU.objects.filter(deleted_date__isnull=True).select_related('brand')
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(brand__name__icontains=q))
    qs = qs.order_by('name')
    total = qs.count()
    items = [{'id': o.pk, 'text': f'{o.name} ({o.brand.name})'} for o in qs[start:end]]
    return items, total


def _os(q, start, end, request):
    qs = OperatingSystem.objects.filter(deleted_date__isnull=True)
    if q: qs = qs.filter(name__icontains=q)
    return _simple(qs.order_by('name'), start, end)


def _accessory_types(q, start, end, request):
    qs = AccessoryType.objects.filter(deleted_date__isnull=True)
    if q: qs = qs.filter(name__icontains=q)
    return _simple(qs.order_by('name'), start, end)


def _sites(q, start, end, request):
    qs = Site.objects.filter(deleted_date__isnull=True).select_related('governorate')
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(governorate__name__icontains=q))
    gov_id = request.GET.get('governorate')
    if gov_id:
        qs = qs.filter(governorate_id=gov_id)
    qs = qs.order_by('governorate__name', 'name')
    total = qs.count()
    items = [{'id': o.pk, 'text': f'{o.name} — {o.governorate.name if o.governorate else ""}'} for o in qs[start:end]]
    return items, total


def _governorates(q, start, end, request):
    qs = Governorate.objects.filter(deleted_date__isnull=True)
    if q: qs = qs.filter(name__icontains=q)
    return _simple(qs.order_by('name'), start, end)


def _devices(q, start, end, request):
    qs = Device.objects.filter(deleted_date__isnull=True).select_related('category', 'brand')
    if q:
        qs = qs.filter(
            Q(serial_number__icontains=q) |
            Q(brand__name__icontains=q) |
            Q(category__name__icontains=q)
        )
    qs = qs.order_by('serial_number')
    total = qs.count()
    items = [{'id': o.pk, 'text': f'{o.serial_number} ({o.category.name} · {o.brand.name})'}
             for o in qs[start:end]]
    return items, total


def _employees(q, start, end, request):
    qs = Employee.objects.filter(deleted_date__isnull=True).select_related('site', 'department')
    if q:
        qs = qs.filter(
            Q(first_name__icontains=q) | Q(last_name__icontains=q) |
            Q(employee_card_id__icontains=q)
        )
    qs = qs.order_by('first_name', 'last_name')
    total = qs.count()
    items = [{'id': o.pk, 'text': f'{o.full_name} ({o.site.name if o.site else ""})'} for o in qs[start:end]]
    return items, total


def _departments(q, start, end, request):
    qs = Department.objects.filter(deleted_date__isnull=True)
    if q: qs = qs.filter(name__icontains=q)
    return _simple(qs.order_by('name'), start, end)
