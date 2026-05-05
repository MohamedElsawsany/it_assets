from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.utils.translation import gettext as _, gettext_lazy as _lazy
from django.views.decorators.http import require_http_methods
from django.db.models import Q

PAGE_SIZE = 10

from .models import User
from .forms import UserCreateForm, UserEditForm, ResetPasswordForm
from .permissions import permission_required, has_permission, Perms


# ── Permission checklist definition ──────────────────────────────────────────
# Describes the groups and rows shown in the edit modal.
# Each entry: (group_label, model_label, [(button_label, django_codename), ...])
# Only permissions relevant to the IT asset app are included.

PERM_GROUPS = [
    (_lazy('Inventory'), [
        (_lazy('Devices'), [
            (_lazy('View'),               'inventory.view_device'),
            (_lazy('Add'),                'inventory.add_device'),
            (_lazy('Edit'),               'inventory.change_device'),
            (_lazy('Delete'),             'inventory.delete_device'),
            (_lazy('Flag'),               'inventory.flag_device'),
            (_lazy('Retire'),             'inventory.retire_device'),
            (_lazy('Toggle Maintenance'), 'inventory.toggle_maintenance'),
            (_lazy('View Specs'),         'inventory.view_device_specs'),
            (_lazy('Export'),             'inventory.export_device'),
            (_lazy('View History'),       'inventory.view_history_device'),
        ]),
        (_lazy('Accessories'), [
            (_lazy('View'),        'inventory.view_accessory'),
            (_lazy('Add'),         'inventory.add_accessory'),
            (_lazy('Edit'),        'inventory.change_accessory'),
            (_lazy('Delete'),      'inventory.delete_accessory'),
            (_lazy('Link Device'), 'inventory.link_device_accessory'),
        ]),
        (_lazy('Lookups'), [
            (_lazy('View'),   'inventory.view_devicecategory'),
            (_lazy('Add'),    'inventory.add_devicecategory'),
            (_lazy('Edit'),   'inventory.change_devicecategory'),
            (_lazy('Delete'), 'inventory.delete_devicecategory'),
        ]),
    ]),
    (_lazy('Assignments'), [
        (_lazy('Assignments'), [
            (_lazy('View'),            'assignments.view_deviceassignment'),
            (_lazy('Add'),             'assignments.add_deviceassignment'),
            (_lazy('Edit'),            'assignments.change_deviceassignment'),
            (_lazy('Delete'),          'assignments.delete_deviceassignment'),
            (_lazy('Return Device'),   'assignments.return_device'),
            (_lazy('Generate Report'), 'assignments.generate_report'),
        ]),
        (_lazy('Transfers'), [
            (_lazy('View'),             'assignments.view_devicetransfer'),
            (_lazy('Add'),              'assignments.add_devicetransfer'),
            (_lazy('Approve Transfer'), 'assignments.approve_transfer'),
            (_lazy('Delete'),           'assignments.delete_devicetransfer'),
        ]),
    ]),
    (_lazy('Maintenance'), [
        (_lazy('Records'), [
            (_lazy('View'),      'maintenance.view_maintenancerecord'),
            (_lazy('Add'),       'maintenance.add_maintenancerecord'),
            (_lazy('Edit'),      'maintenance.change_maintenancerecord'),
            (_lazy('Delete'),    'maintenance.delete_maintenancerecord'),
            (_lazy('Close'),     'maintenance.close_maintenancerecord'),
            (_lazy('View Cost'), 'maintenance.view_cost'),
            (_lazy('Export'),    'maintenance.export_maintenancerecord'),
        ]),
    ]),
    (_lazy('Organization'), [
        (_lazy('Employees'), [
            (_lazy('View'),     'employees.view_employee'),
            (_lazy('Add'),      'employees.add_employee'),
            (_lazy('Edit'),     'employees.change_employee'),
            (_lazy('Delete'),   'employees.delete_employee'),
            (_lazy('Transfer'), 'employees.transfer_employee'),
        ]),
        (_lazy('Locations'), [
            (_lazy('View'),   'locations.view_site'),
            (_lazy('Add'),    'locations.add_site'),
            (_lazy('Edit'),   'locations.change_site'),
            (_lazy('Delete'), 'locations.delete_site'),
        ]),
    ]),
    (_lazy('System'), [
        (_lazy('Users'), [
            (_lazy('View'),           'accounts.view_user'),
            (_lazy('Add'),            'accounts.add_user'),
            (_lazy('Edit'),           'accounts.change_user'),
            (_lazy('Delete'),         'accounts.delete_user'),
            (_lazy('Reset Password'), 'accounts.reset_password_user'),
            (_lazy('Activate'),       'accounts.activate_user'),
        ]),
    ]),
]


@login_required
@permission_required(Perms.USERS_VIEW)
def users_list(request):
    from locations.models import Site
    return render(request, 'accounts/users.html', {
        'sites': Site.objects.all().order_by('name'),
    })


@login_required
@permission_required(Perms.USERS_VIEW)
def users_data(request):
    search        = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status', '').strip()

    qs = User.objects.filter(deleted_date__isnull=True).select_related('site')

    if search:
        qs = qs.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search)
        )
    if status_filter == 'active':
        qs = qs.filter(is_active=True)
    elif status_filter == 'inactive':
        qs = qs.filter(is_active=False)

    qs = qs.order_by('-created_date')
    paginator = Paginator(qs, PAGE_SIZE)
    try:
        page_num = int(request.GET.get('page', 1))
    except (ValueError, TypeError):
        page_num = 1
    page_obj  = paginator.get_page(page_num)

    users = []
    for user in page_obj:
        users.append({
            'id':           user.pk,
            'full_name':    user.full_name,
            'first_name':   user.first_name,
            'last_name':    user.last_name,
            'email':        user.email,
            'site_id':      user.site_id or '',
            'site_name':    user.site.name if user.site else '',
            'is_active':    user.is_active,
            'created_date': user.created_date.strftime('%Y-%m-%d') if user.created_date else '',
        })

    return JsonResponse({'success': True, 'users': users, 'total': paginator.count,
                         'page': page_obj.number, 'num_pages': paginator.num_pages})


@login_required
def user_detail(request, user_id):
    if not has_permission(request.user, Perms.USERS_VIEW):
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)

    user = get_object_or_404(User.objects.select_related('site', 'created_by', 'updated_by'), pk=user_id, deleted_date__isnull=True)
    return JsonResponse({
        'success': True,
        'user': {
            'id':          user.pk,
            'first_name':  user.first_name,
            'last_name':   user.last_name,
            'full_name':   user.full_name,
            'email':       user.email,
            'site_id':     user.site_id or '',
            'site_name':   user.site.name if user.site else '',
            'is_active':   user.is_active,
            'is_superuser': user.is_superuser,
            # Site scope fields
            'site_scope':       user.site_scope,
            'own_site_id':      user.own_site_id or '',
            'allowed_site_ids': list(user.allowed_sites.values_list('id', flat=True)),
            # Audit
            'created_by':   user.created_by.full_name if user.created_by else '',
            'created_date': user.created_date.strftime('%Y-%m-%d %I:%M %p') if user.created_date else '',
            'updated_by':   user.updated_by.full_name if user.updated_by else '',
            'updated_date': user.updated_date.strftime('%Y-%m-%d %I:%M %p') if user.updated_date else '',
        }
    })


@login_required
@require_http_methods(['POST'])
def user_create(request):
    if not has_permission(request.user, Perms.USERS_CREATE):
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)

    form = UserCreateForm(request.POST)
    if form.is_valid():
        user = form.save(commit=False)
        user.created_by = request.user
        user.save()
        return JsonResponse({'success': True, 'message': _('User created successfully.')})

    errors = {field: [str(e) for e in errs] for field, errs in form.errors.items()}
    return JsonResponse({'success': False, 'errors': errors})


@login_required
@require_http_methods(['POST'])
def user_edit(request, user_id):
    if not has_permission(request.user, Perms.USERS_EDIT):
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)

    user = get_object_or_404(User, pk=user_id, deleted_date__isnull=True)
    form = UserEditForm(request.POST, instance=user)
    if form.is_valid():
        obj = form.save(commit=False)
        obj.updated_by = request.user
        obj.save()
        return JsonResponse({'success': True, 'message': _('User updated successfully.')})

    errors = {field: [str(e) for e in errs] for field, errs in form.errors.items()}
    return JsonResponse({'success': False, 'errors': errors})


@login_required
@require_http_methods(['POST'])
def user_delete(request, user_id):
    if not has_permission(request.user, Perms.USERS_DELETE):
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)

    user = get_object_or_404(User, pk=user_id, deleted_date__isnull=True)
    if user.pk == request.user.pk:
        return JsonResponse({'success': False, 'message': _('You cannot delete your own account.')})
    if user.assigned_devices.exists():
        return JsonResponse({'success': False, 'message': _('Cannot delete: user has assignment records.')})
    if user.device_transfers.exists():
        return JsonResponse({'success': False, 'message': _('Cannot delete: user has transfer records.')})

    from django.utils import timezone
    user.deleted_date = timezone.now()
    user.is_active = False
    user.save()
    return JsonResponse({'success': True, 'message': _('User deleted successfully.')})


@login_required
@require_http_methods(['POST'])
def user_toggle_status(request, user_id):
    if not has_permission(request.user, Perms.USERS_ACTIVATE):
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)

    user = get_object_or_404(User, pk=user_id, deleted_date__isnull=True)
    if user.pk == request.user.pk:
        return JsonResponse({'success': False, 'message': _('You cannot change your own status.')})

    user.is_active = not user.is_active
    user.save()
    return JsonResponse({
        'success': True,
        'message': _('User activated.') if user.is_active else _('User deactivated.'),
        'is_active': user.is_active,
    })


@login_required
@require_http_methods(['POST'])
def user_reset_password(request, user_id):
    if not has_permission(request.user, Perms.USERS_RESET_PASSWORD):
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)

    user = get_object_or_404(User, pk=user_id, deleted_date__isnull=True)
    form = ResetPasswordForm(request.POST)
    if form.is_valid():
        user.set_password(form.cleaned_data['new_password'])
        user.save()
        return JsonResponse({'success': True, 'message': _('Password reset successfully.')})

    errors = {field: [str(e) for e in errs] for field, errs in form.errors.items()}
    return JsonResponse({'success': False, 'errors': errors})


# ── Permission management ─────────────────────────────────────────────────────

@login_required
def user_permissions(request, user_id):
    """
    GET  → returns the permission checklist structure with the target user's
           current grants pre-marked.
    POST → saves the submitted permission_ids to user.user_permissions.
    """
    if not has_permission(request.user, Perms.USERS_EDIT):
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)

    target = get_object_or_404(User, pk=user_id, deleted_date__isnull=True)

    if request.method == 'GET':
        # Build a flat map: 'app.codename' → Permission.id
        perm_lookup = {}
        for p in Permission.objects.select_related('content_type').all():
            key = f'{p.content_type.app_label}.{p.codename}'
            perm_lookup[key] = p.id

        # Current grants for this user
        current_ids = set(
            target.user_permissions.values_list('id', flat=True)
        )

        # Build the structured checklist from PERM_GROUPS
        groups = []
        for group_label, models in PERM_GROUPS:
            model_rows = []
            for model_label, perms in models:
                buttons = []
                for btn_label, codename in perms:
                    pid = perm_lookup.get(codename)
                    buttons.append({
                        'label':    btn_label,
                        'codename': codename,
                        'id':       pid,
                        'granted':  pid in current_ids if pid else False,
                    })
                model_rows.append({'model': model_label, 'perms': buttons})
            groups.append({'group': group_label, 'models': model_rows})

        return JsonResponse({
            'success': True,
            'is_superuser': target.is_superuser,
            'groups': groups,
        })

    # POST — save selected permissions
    if request.method == 'POST':
        raw_ids = request.POST.getlist('permission_ids')
        try:
            perm_ids = [int(x) for x in raw_ids if x]
        except ValueError:
            return JsonResponse({'success': False, 'message': _('Invalid permission IDs.')}, status=400)

        # Verify every submitted ID is in our managed set (security: don't let
        # callers grant arbitrary Django admin/session/etc. permissions).
        allowed_codenames = {
            codename
            for _, models in PERM_GROUPS
            for _, perms in models
            for _, codename in perms
        }
        allowed_ids = set(
            Permission.objects.filter(
                content_type__app_label__in=[c.split('.')[0] for c in allowed_codenames]
            ).filter(
                id__in=perm_ids
            ).values_list('id', flat=True)
        )

        target.user_permissions.set(allowed_ids)
        # Clear Django's permission cache for this user
        if hasattr(target, '_perm_cache'):
            del target._perm_cache
        if hasattr(target, '_user_perm_cache'):
            del target._user_perm_cache

        return JsonResponse({'success': True, 'message': _('Permissions saved.')})

    return JsonResponse({'success': False, 'message': _('Method not allowed.')}, status=405)


@login_required
@require_http_methods(['POST'])
def user_scope_save(request, user_id):
    """
    Save site_scope + own_site / allowed_sites for a user.
    """
    if not has_permission(request.user, Perms.USERS_EDIT):
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)

    target = get_object_or_404(User, pk=user_id, deleted_date__isnull=True)

    scope = request.POST.get('site_scope', User.SiteScope.OWN)
    if scope not in User.SiteScope.values:
        return JsonResponse({'success': False, 'message': _('Invalid site scope.')}, status=400)

    from locations.models import Site

    target.site_scope = scope

    if scope == User.SiteScope.OWN:
        own_site_id = request.POST.get('own_site') or None
        if own_site_id:
            target.own_site = get_object_or_404(Site, pk=own_site_id)
        else:
            target.own_site = None
        target.allowed_sites.clear()

    elif scope == User.SiteScope.SPECIFIC:
        site_ids = request.POST.getlist('allowed_sites')
        target.own_site = None
        target.save()
        target.allowed_sites.set(Site.objects.filter(pk__in=site_ids))

    elif scope == User.SiteScope.ALL:
        target.own_site = None
        target.allowed_sites.clear()

    target.save()
    return JsonResponse({'success': True, 'message': _('Site access saved.')})
