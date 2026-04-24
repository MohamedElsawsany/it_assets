from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods
from django.db.models import Q

PAGE_SIZE = 10

from .models import User
from .forms import UserCreateForm, UserEditForm, ResetPasswordForm
from .permissions import permission_required, has_permission, Perms


@login_required
@permission_required(Perms.USERS_VIEW)
def users_list(request):
    from locations.models import Site
    return render(request, 'accounts/users.html', {
        'role_choices': User.ROLE_CHOICES,
        'sites': Site.objects.all().order_by('name'),
    })


@login_required
@permission_required(Perms.USERS_VIEW)
def users_data(request):
    search = request.GET.get('search', '').strip()
    role_filter = request.GET.get('role', '').strip()
    status_filter = request.GET.get('status', '').strip()

    qs = User.objects.filter(deleted_date__isnull=True).select_related('site')

    if search:
        qs = qs.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search)
        )
    if role_filter:
        qs = qs.filter(role=role_filter)
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
            'id': user.pk,
            'full_name': user.full_name,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'role': user.role,
            'role_display': user.get_role_display(),
            'role_color': user.role_color,
            'site_id': user.site_id or '',
            'site_name': user.site.name if user.site else '',
            'is_active': user.is_active,
            'created_date': user.created_date.strftime('%Y-%m-%d') if user.created_date else '',
        })

    return JsonResponse({'success': True, 'users': users, 'total': paginator.count,
                         'page': page_obj.number, 'num_pages': paginator.num_pages})


@login_required
def user_detail(request, user_id):
    if not has_permission(request.user, Perms.USERS_VIEW):
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)

    user = get_object_or_404(User.objects.select_related('site', 'created_by'), pk=user_id, deleted_date__isnull=True)
    return JsonResponse({
        'success': True,
        'user': {
            'id': user.pk,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'full_name': user.full_name,
            'email': user.email,
            'role': user.role,
            'role_display': user.get_role_display(),
            'role_color': user.role_color,
            'site_id': user.site_id or '',
            'site_name': user.site.name if user.site else '',
            'is_active': user.is_active,
            'created_by': user.created_by.full_name if user.created_by else '',
            'created_date': user.created_date.strftime('%Y-%m-%d %H:%M') if user.created_date else '',
            'updated_date': user.updated_date.strftime('%Y-%m-%d %H:%M') if user.updated_date else '',
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
        form.save()
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
