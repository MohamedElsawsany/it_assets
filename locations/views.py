from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db.models import Q, Count

PAGE_SIZE = 10

from accounts.permissions import permission_required, has_permission, Perms
from .models import Governorate, Site
from .forms import GovernorateForm, SiteForm


@login_required
@permission_required(Perms.LOCATIONS_VIEW)
def locations_index(request):
    return render(request, 'locations/index.html', {
        'governorates': Governorate.objects.filter(deleted_date__isnull=True).order_by('name'),
    })


# ── Governorates ──────────────────────────────────────────────────────────────

@login_required
@permission_required(Perms.LOCATIONS_VIEW)
def governorates_data(request):
    search = request.GET.get('search', '').strip()
    qs = Governorate.objects.filter(deleted_date__isnull=True).annotate(
        sites_count=Count('sites', filter=Q(sites__deleted_date__isnull=True))
    )
    if search:
        qs = qs.filter(name__icontains=search)
    qs = qs.order_by('name')
    paginator = Paginator(qs, PAGE_SIZE)
    try:
        page_num = int(request.GET.get('page', 1))
    except (ValueError, TypeError):
        page_num = 1
    page_obj  = paginator.get_page(page_num)
    items = [
        {'id': g.pk, 'name': g.name,
         'sites_count': g.sites_count,
         'created_date': g.created_date.strftime('%Y-%m-%d')}
        for g in page_obj
    ]
    return JsonResponse({'success': True, 'items': items, 'total': paginator.count,
                         'page': page_obj.number, 'num_pages': paginator.num_pages})


@login_required
def governorate_detail(request, pk):
    if not has_permission(request.user, Perms.LOCATIONS_VIEW):
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)
    gov = get_object_or_404(Governorate.objects.select_related('created_by', 'updated_by'), pk=pk, deleted_date__isnull=True)
    return JsonResponse({'success': True, 'item': {
        'id': gov.pk, 'name': gov.name,
        'created_by': gov.created_by.full_name,
        'created_date': gov.created_date.strftime('%Y-%m-%d %I:%M %p'),
        'updated_by': gov.updated_by.full_name if gov.updated_by else '',
        'updated_date': gov.updated_date.strftime('%Y-%m-%d %I:%M %p') if gov.updated_date else '',
    }})


@login_required
@require_http_methods(['POST'])
def governorate_create(request):
    if not has_permission(request.user, Perms.LOCATIONS_CREATE):
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)
    form = GovernorateForm(request.POST)
    if form.is_valid():
        obj = form.save(commit=False)
        obj.created_by = request.user
        obj.save()
        return JsonResponse({'success': True, 'message': _('Governorate created successfully.')})
    errors = {f: [str(e) for e in v] for f, v in form.errors.items()}
    return JsonResponse({'success': False, 'errors': errors})


@login_required
@require_http_methods(['POST'])
def governorate_edit(request, pk):
    if not has_permission(request.user, Perms.LOCATIONS_EDIT):
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)
    gov = get_object_or_404(Governorate, pk=pk, deleted_date__isnull=True)
    form = GovernorateForm(request.POST, instance=gov)
    if form.is_valid():
        obj = form.save(commit=False)
        obj.updated_by = request.user
        obj.save()
        return JsonResponse({'success': True, 'message': _('Governorate updated successfully.')})
    errors = {f: [str(e) for e in v] for f, v in form.errors.items()}
    return JsonResponse({'success': False, 'errors': errors})


@login_required
@require_http_methods(['POST'])
def governorate_delete(request, pk):
    if not has_permission(request.user, Perms.LOCATIONS_DELETE):
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)
    gov = get_object_or_404(Governorate, pk=pk, deleted_date__isnull=True)
    if gov.sites.filter(deleted_date__isnull=True).exists():
        return JsonResponse({'success': False, 'message': _('Cannot delete: governorate has active sites.')})
    gov.deleted_date = timezone.now()
    gov.save()
    return JsonResponse({'success': True, 'message': _('Governorate deleted successfully.')})


# ── Sites ─────────────────────────────────────────────────────────────────────

@login_required
@permission_required(Perms.LOCATIONS_VIEW)
def sites_data(request):
    search = request.GET.get('search', '').strip()
    gov_id = request.GET.get('governorate', '').strip()
    qs = Site.objects.filter(deleted_date__isnull=True).select_related('governorate')
    if search:
        qs = qs.filter(Q(name__icontains=search) | Q(governorate__name__icontains=search))
    if gov_id:
        qs = qs.filter(governorate_id=gov_id)
    qs = qs.order_by('governorate__name', 'name')
    paginator = Paginator(qs, PAGE_SIZE)
    try:
        page_num = int(request.GET.get('page', 1))
    except (ValueError, TypeError):
        page_num = 1
    page_obj  = paginator.get_page(page_num)
    items = [
        {'id': s.pk, 'name': s.name,
         'governorate_id': s.governorate_id,
         'governorate_name': s.governorate.name,
         'created_date': s.created_date.strftime('%Y-%m-%d')}
        for s in page_obj
    ]
    return JsonResponse({'success': True, 'items': items, 'total': paginator.count,
                         'page': page_obj.number, 'num_pages': paginator.num_pages})


@login_required
def site_detail(request, pk):
    if not has_permission(request.user, Perms.LOCATIONS_VIEW):
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)
    site = get_object_or_404(Site.objects.select_related('governorate', 'created_by', 'updated_by'),
                             pk=pk, deleted_date__isnull=True)
    return JsonResponse({'success': True, 'item': {
        'id': site.pk, 'name': site.name,
        'governorate_id': site.governorate_id, 'governorate_name': site.governorate.name,
        'created_by': site.created_by.full_name,
        'created_date': site.created_date.strftime('%Y-%m-%d %I:%M %p'),
        'updated_by': site.updated_by.full_name if site.updated_by else '',
        'updated_date': site.updated_date.strftime('%Y-%m-%d %I:%M %p') if site.updated_date else '',
    }})


@login_required
@require_http_methods(['POST'])
def site_create(request):
    if not has_permission(request.user, Perms.LOCATIONS_CREATE):
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)
    form = SiteForm(request.POST)
    if form.is_valid():
        obj = form.save(commit=False)
        obj.created_by = request.user
        obj.save()
        return JsonResponse({'success': True, 'message': _('Site created successfully.')})
    errors = {f: [str(e) for e in v] for f, v in form.errors.items()}
    return JsonResponse({'success': False, 'errors': errors})


@login_required
@require_http_methods(['POST'])
def site_edit(request, pk):
    if not has_permission(request.user, Perms.LOCATIONS_EDIT):
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)
    site = get_object_or_404(Site, pk=pk, deleted_date__isnull=True)
    form = SiteForm(request.POST, instance=site)
    if form.is_valid():
        obj = form.save(commit=False)
        obj.updated_by = request.user
        obj.save()
        return JsonResponse({'success': True, 'message': _('Site updated successfully.')})
    errors = {f: [str(e) for e in v] for f, v in form.errors.items()}
    return JsonResponse({'success': False, 'errors': errors})


@login_required
@require_http_methods(['POST'])
def site_delete(request, pk):
    if not has_permission(request.user, Perms.LOCATIONS_DELETE):
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)
    site = get_object_or_404(Site, pk=pk, deleted_date__isnull=True)
    if site.devices.filter(deleted_date__isnull=True).exists():
        return JsonResponse({'success': False, 'message': _('Cannot delete: site has devices.')})
    if site.accessories.filter(deleted_date__isnull=True).exists():
        return JsonResponse({'success': False, 'message': _('Cannot delete: site has accessories.')})
    if site.employees.filter(deleted_date__isnull=True).exists():
        return JsonResponse({'success': False, 'message': _('Cannot delete: site has employees.')})
    if site.users.filter(deleted_date__isnull=True).exists():
        return JsonResponse({'success': False, 'message': _('Cannot delete: site has users.')})
    if site.outgoing_transfers.exists() or site.incoming_transfers.exists():
        return JsonResponse({'success': False, 'message': _('Cannot delete: site has transfer records.')})
    site.deleted_date = timezone.now()
    site.save()
    return JsonResponse({'success': True, 'message': _('Site deleted successfully.')})
