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
from locations.models import Site
from .models import Department, Employee
from .forms import DepartmentForm, EmployeeForm


@login_required
@permission_required(Perms.EMPLOYEES_VIEW)
def employees_index(request):
    return render(request, 'employees/index.html', {
        'sites':       Site.objects.filter(deleted_date__isnull=True).order_by('name'),
        'departments': Department.objects.filter(deleted_date__isnull=True).order_by('name'),
    })


# ── Departments ───────────────────────────────────────────────────────────────

@login_required
@permission_required(Perms.EMPLOYEES_VIEW)
def departments_data(request):
    search = request.GET.get('search', '').strip()
    qs = Department.objects.filter(deleted_date__isnull=True).annotate(
        employees_count=Count('employees', filter=Q(employees__deleted_date__isnull=True))
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
        {'id': d.pk, 'name': d.name,
         'employees_count': d.employees_count,
         'created_date': d.created_date.strftime('%Y-%m-%d')}
        for d in page_obj
    ]
    return JsonResponse({'success': True, 'items': items, 'total': paginator.count,
                         'page': page_obj.number, 'num_pages': paginator.num_pages})


@login_required
def department_detail(request, pk):
    if not has_permission(request.user, Perms.EMPLOYEES_VIEW):
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)
    dept = get_object_or_404(Department.objects.select_related('created_by'), pk=pk, deleted_date__isnull=True)
    return JsonResponse({'success': True, 'item': {
        'id': dept.pk, 'name': dept.name,
        'created_by': dept.created_by.full_name,
        'created_date': dept.created_date.strftime('%Y-%m-%d %I:%M %p'),
        'updated_date': dept.updated_date.strftime('%Y-%m-%d %I:%M %p') if dept.updated_date else '',
    }})


@login_required
@require_http_methods(['POST'])
def department_create(request):
    if not has_permission(request.user, Perms.EMPLOYEES_CREATE):
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)
    form = DepartmentForm(request.POST)
    if form.is_valid():
        obj = form.save(commit=False)
        obj.created_by = request.user
        obj.save()
        return JsonResponse({'success': True, 'message': _('Department created successfully.')})
    errors = {f: [str(e) for e in v] for f, v in form.errors.items()}
    return JsonResponse({'success': False, 'errors': errors})


@login_required
@require_http_methods(['POST'])
def department_edit(request, pk):
    if not has_permission(request.user, Perms.EMPLOYEES_EDIT):
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)
    dept = get_object_or_404(Department, pk=pk, deleted_date__isnull=True)
    form = DepartmentForm(request.POST, instance=dept)
    if form.is_valid():
        form.save()
        return JsonResponse({'success': True, 'message': _('Department updated successfully.')})
    errors = {f: [str(e) for e in v] for f, v in form.errors.items()}
    return JsonResponse({'success': False, 'errors': errors})


@login_required
@require_http_methods(['POST'])
def department_delete(request, pk):
    if not has_permission(request.user, Perms.EMPLOYEES_DELETE):
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)
    dept = get_object_or_404(Department, pk=pk, deleted_date__isnull=True)
    if dept.employees.filter(deleted_date__isnull=True).exists():
        return JsonResponse({'success': False, 'message': _('Cannot delete: department has active employees.')})
    dept.deleted_date = timezone.now()
    dept.save()
    return JsonResponse({'success': True, 'message': _('Department deleted successfully.')})


# ── Employees ─────────────────────────────────────────────────────────────────

@login_required
@permission_required(Perms.EMPLOYEES_VIEW)
def employees_data(request):
    search  = request.GET.get('search', '').strip()
    dept_id = request.GET.get('department', '').strip()
    site_id = request.GET.get('site', '').strip()
    qs = Employee.objects.filter(deleted_date__isnull=True).select_related('department', 'site')
    if search:
        qs = qs.filter(
            Q(first_name__icontains=search) | Q(last_name__icontains=search) |
            Q(employee_card_id__icontains=search)
        )
    if dept_id:
        qs = qs.filter(department_id=dept_id)
    if site_id:
        qs = qs.filter(site_id=site_id)
    qs = qs.order_by('first_name', 'last_name')
    paginator = Paginator(qs, PAGE_SIZE)
    try:
        page_num = int(request.GET.get('page', 1))
    except (ValueError, TypeError):
        page_num = 1
    page_obj  = paginator.get_page(page_num)
    items = [
        {'id': e.pk, 'full_name': e.full_name,
         'first_name': e.first_name, 'last_name': e.last_name,
         'employee_card_id': e.employee_card_id,
         'department_id': e.department_id, 'department_name': e.department.name,
         'site_id': e.site_id, 'site_name': e.site.name,
         'created_date': e.created_date.strftime('%Y-%m-%d')}
        for e in page_obj
    ]
    return JsonResponse({'success': True, 'items': items, 'total': paginator.count,
                         'page': page_obj.number, 'num_pages': paginator.num_pages})


@login_required
def employee_detail(request, pk):
    if not has_permission(request.user, Perms.EMPLOYEES_VIEW):
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)
    emp = get_object_or_404(Employee.objects.select_related('department', 'site', 'created_by'),
                            pk=pk, deleted_date__isnull=True)
    return JsonResponse({'success': True, 'item': {
        'id': emp.pk, 'first_name': emp.first_name, 'last_name': emp.last_name,
        'employee_card_id': emp.employee_card_id,
        'department_id': emp.department_id, 'department_name': emp.department.name,
        'site_id': emp.site_id,             'site_name': emp.site.name,
        'created_by': emp.created_by.full_name,
        'created_date': emp.created_date.strftime('%Y-%m-%d %I:%M %p'),
        'updated_date': emp.updated_date.strftime('%Y-%m-%d %I:%M %p') if emp.updated_date else '',
    }})


@login_required
@require_http_methods(['POST'])
def employee_create(request):
    if not has_permission(request.user, Perms.EMPLOYEES_CREATE):
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)
    form = EmployeeForm(request.POST)
    if form.is_valid():
        obj = form.save(commit=False)
        obj.created_by = request.user
        obj.save()
        return JsonResponse({'success': True, 'message': _('Employee created successfully.')})
    errors = {f: [str(e) for e in v] for f, v in form.errors.items()}
    return JsonResponse({'success': False, 'errors': errors})


@login_required
@require_http_methods(['POST'])
def employee_edit(request, pk):
    if not has_permission(request.user, Perms.EMPLOYEES_EDIT):
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)
    emp = get_object_or_404(Employee, pk=pk, deleted_date__isnull=True)
    form = EmployeeForm(request.POST, instance=emp)
    if form.is_valid():
        form.save()
        return JsonResponse({'success': True, 'message': _('Employee updated successfully.')})
    errors = {f: [str(e) for e in v] for f, v in form.errors.items()}
    return JsonResponse({'success': False, 'errors': errors})


@login_required
@require_http_methods(['POST'])
def employee_delete(request, pk):
    if not has_permission(request.user, Perms.EMPLOYEES_DELETE):
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)
    emp = get_object_or_404(Employee, pk=pk, deleted_date__isnull=True)
    if emp.assignments.exists():
        return JsonResponse({'success': False, 'message': _('Cannot delete: employee has assignment records.')})
    emp.deleted_date = timezone.now()
    emp.save()
    return JsonResponse({'success': True, 'message': _('Employee deleted successfully.')})
