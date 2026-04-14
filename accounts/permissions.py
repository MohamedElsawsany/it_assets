"""
accounts/permissions.py
───────────────────────
42 permissions across 8 roles covering every model and action in the system.
Site-scoped access control via ROLE_SITE_SCOPE + get_site_filter().

Quick reference
───────────────
  from accounts.permissions import has_permission, permission_required, Perms
  from accounts.permissions import get_site_filter, sees_all_sites

  # guard a view
  @permission_required(Perms.DEVICES_CREATE)
  def add_device(request): ...

  # guard a code path
  if has_permission(request.user, Perms.MAINTENANCE_VIEW_COST):
      ...

  # site-scoped queryset — works on any model with a direct `site` FK
  devices = Device.objects.filter(**get_site_filter(request.user))

  # site-scoped queryset — model with indirect site (via related field)
  assignments = DeviceAssignment.objects.filter(**get_site_filter(request.user, prefix='device__'))

  # templates — injected automatically by context_processors.py
  {% if rbac.devices_create %} ... {% endif %}
  {% if rbac.sees_all_sites %} ... {% endif %}
"""

from functools import wraps
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect


# ══════════════════════════════════════════════════════════════════════════════
# PERMISSION CONSTANTS
# ══════════════════════════════════════════════════════════════════════════════

class Perms:

    # ── Users / Accounts (7) ──────────────────────────────────────────────────
    USERS_VIEW               = 'users.view'
    USERS_CREATE             = 'users.create'
    USERS_EDIT               = 'users.edit'
    USERS_DELETE             = 'users.delete'
    USERS_ASSIGN_ROLE        = 'users.assign_role'
    USERS_RESET_PASSWORD     = 'users.reset_password'
    USERS_ACTIVATE           = 'users.activate'

    # ── Locations — Governorates + Sites (4) ─────────────────────────────────
    LOCATIONS_VIEW           = 'locations.view'
    LOCATIONS_CREATE         = 'locations.create'
    LOCATIONS_EDIT           = 'locations.edit'
    LOCATIONS_DELETE         = 'locations.delete'

    # ── Employees + Departments (5) ───────────────────────────────────────────
    EMPLOYEES_VIEW           = 'employees.view'
    EMPLOYEES_CREATE         = 'employees.create'
    EMPLOYEES_EDIT           = 'employees.edit'
    EMPLOYEES_DELETE         = 'employees.delete'
    EMPLOYEES_TRANSFER       = 'employees.transfer'

    # ── Lookup tables (4) ─────────────────────────────────────────────────────
    LOOKUPS_VIEW             = 'lookups.view'
    LOOKUPS_CREATE           = 'lookups.create'
    LOOKUPS_EDIT             = 'lookups.edit'
    LOOKUPS_DELETE           = 'lookups.delete'

    # ── Devices (10) ──────────────────────────────────────────────────────────
    DEVICES_VIEW             = 'devices.view'
    DEVICES_CREATE           = 'devices.create'
    DEVICES_EDIT             = 'devices.edit'
    DEVICES_DELETE           = 'devices.delete'
    DEVICES_VIEW_SPECS       = 'devices.view_specs'
    DEVICES_RETIRE           = 'devices.retire'
    DEVICES_CHANGE_FLAG      = 'devices.change_flag'
    DEVICES_TOGGLE_MAINTENANCE = 'devices.toggle_maintenance'
    DEVICES_EXPORT           = 'devices.export'
    DEVICES_VIEW_HISTORY     = 'devices.view_history'

    # ── Accessories (5) ───────────────────────────────────────────────────────
    ACCESSORIES_VIEW         = 'accessories.view'
    ACCESSORIES_CREATE       = 'accessories.create'
    ACCESSORIES_EDIT         = 'accessories.edit'
    ACCESSORIES_DELETE       = 'accessories.delete'
    ACCESSORIES_LINK_DEVICE  = 'accessories.link_device'

    # ── Assignments (6) ───────────────────────────────────────────────────────
    ASSIGNMENTS_VIEW         = 'assignments.view'
    ASSIGNMENTS_CREATE       = 'assignments.create'
    ASSIGNMENTS_EDIT         = 'assignments.edit'
    ASSIGNMENTS_DELETE       = 'assignments.delete'
    ASSIGNMENTS_RETURN       = 'assignments.return'
    ASSIGNMENTS_EXPORT       = 'assignments.export'

    # ── Transfers (4) ─────────────────────────────────────────────────────────
    TRANSFERS_VIEW           = 'transfers.view'
    TRANSFERS_CREATE         = 'transfers.create'
    TRANSFERS_APPROVE        = 'transfers.approve'
    TRANSFERS_DELETE         = 'transfers.delete'

    # ── Maintenance (7) ───────────────────────────────────────────────────────
    MAINTENANCE_VIEW         = 'maintenance.view'
    MAINTENANCE_CREATE       = 'maintenance.create'
    MAINTENANCE_EDIT         = 'maintenance.edit'
    MAINTENANCE_DELETE       = 'maintenance.delete'
    MAINTENANCE_CLOSE        = 'maintenance.close'
    MAINTENANCE_VIEW_COST    = 'maintenance.view_cost'
    MAINTENANCE_EXPORT       = 'maintenance.export'

    ALL = [
        USERS_VIEW, USERS_CREATE, USERS_EDIT, USERS_DELETE,
        USERS_ASSIGN_ROLE, USERS_RESET_PASSWORD, USERS_ACTIVATE,

        LOCATIONS_VIEW, LOCATIONS_CREATE, LOCATIONS_EDIT, LOCATIONS_DELETE,

        EMPLOYEES_VIEW, EMPLOYEES_CREATE, EMPLOYEES_EDIT,
        EMPLOYEES_DELETE, EMPLOYEES_TRANSFER,

        LOOKUPS_VIEW, LOOKUPS_CREATE, LOOKUPS_EDIT, LOOKUPS_DELETE,

        DEVICES_VIEW, DEVICES_CREATE, DEVICES_EDIT, DEVICES_DELETE,
        DEVICES_VIEW_SPECS, DEVICES_RETIRE, DEVICES_CHANGE_FLAG,
        DEVICES_TOGGLE_MAINTENANCE, DEVICES_EXPORT, DEVICES_VIEW_HISTORY,

        ACCESSORIES_VIEW, ACCESSORIES_CREATE, ACCESSORIES_EDIT,
        ACCESSORIES_DELETE, ACCESSORIES_LINK_DEVICE,

        ASSIGNMENTS_VIEW, ASSIGNMENTS_CREATE, ASSIGNMENTS_EDIT,
        ASSIGNMENTS_DELETE, ASSIGNMENTS_RETURN, ASSIGNMENTS_EXPORT,

        TRANSFERS_VIEW, TRANSFERS_CREATE, TRANSFERS_APPROVE, TRANSFERS_DELETE,

        MAINTENANCE_VIEW, MAINTENANCE_CREATE, MAINTENANCE_EDIT,
        MAINTENANCE_DELETE, MAINTENANCE_CLOSE,
        MAINTENANCE_VIEW_COST, MAINTENANCE_EXPORT,
    ]


# ══════════════════════════════════════════════════════════════════════════════
# ROLE → PERMISSION MAPPING
# ══════════════════════════════════════════════════════════════════════════════

P = Perms

ROLE_PERMISSIONS = {

    # ── 1. Super Admin ────────────────────────────────────────────────────────
    'super_admin': None,

    # ── 2. IT Admin ───────────────────────────────────────────────────────────
    'it_admin': {
        P.USERS_VIEW, P.USERS_CREATE, P.USERS_EDIT,
        P.USERS_DELETE, P.USERS_RESET_PASSWORD, P.USERS_ACTIVATE,

        P.LOCATIONS_VIEW, P.LOCATIONS_CREATE, P.LOCATIONS_EDIT, P.LOCATIONS_DELETE,

        P.EMPLOYEES_VIEW, P.EMPLOYEES_CREATE, P.EMPLOYEES_EDIT,
        P.EMPLOYEES_DELETE, P.EMPLOYEES_TRANSFER,

        P.LOOKUPS_VIEW, P.LOOKUPS_CREATE, P.LOOKUPS_EDIT, P.LOOKUPS_DELETE,

        P.DEVICES_VIEW, P.DEVICES_CREATE, P.DEVICES_EDIT, P.DEVICES_DELETE,
        P.DEVICES_VIEW_SPECS, P.DEVICES_RETIRE, P.DEVICES_CHANGE_FLAG,
        P.DEVICES_TOGGLE_MAINTENANCE, P.DEVICES_EXPORT, P.DEVICES_VIEW_HISTORY,

        P.ACCESSORIES_VIEW, P.ACCESSORIES_CREATE, P.ACCESSORIES_EDIT,
        P.ACCESSORIES_DELETE, P.ACCESSORIES_LINK_DEVICE,

        P.ASSIGNMENTS_VIEW, P.ASSIGNMENTS_CREATE, P.ASSIGNMENTS_EDIT,
        P.ASSIGNMENTS_DELETE, P.ASSIGNMENTS_RETURN, P.ASSIGNMENTS_EXPORT,

        P.TRANSFERS_VIEW, P.TRANSFERS_CREATE,
        P.TRANSFERS_APPROVE, P.TRANSFERS_DELETE,

        P.MAINTENANCE_VIEW, P.MAINTENANCE_CREATE, P.MAINTENANCE_EDIT,
        P.MAINTENANCE_DELETE, P.MAINTENANCE_CLOSE,
        P.MAINTENANCE_VIEW_COST, P.MAINTENANCE_EXPORT,
    },

    # ── 3. IT Supervisor ──────────────────────────────────────────────────────
    'it_supervisor': {
        P.USERS_VIEW,

        P.LOCATIONS_VIEW,

        P.EMPLOYEES_VIEW, P.EMPLOYEES_TRANSFER,

        P.LOOKUPS_VIEW,

        P.DEVICES_VIEW, P.DEVICES_VIEW_SPECS,
        P.DEVICES_CHANGE_FLAG, P.DEVICES_TOGGLE_MAINTENANCE,
        P.DEVICES_EXPORT, P.DEVICES_VIEW_HISTORY,

        P.ACCESSORIES_VIEW,

        P.ASSIGNMENTS_VIEW, P.ASSIGNMENTS_CREATE, P.ASSIGNMENTS_EDIT,
        P.ASSIGNMENTS_RETURN, P.ASSIGNMENTS_EXPORT,

        P.TRANSFERS_VIEW, P.TRANSFERS_APPROVE,

        P.MAINTENANCE_VIEW, P.MAINTENANCE_EDIT,
        P.MAINTENANCE_CLOSE, P.MAINTENANCE_VIEW_COST, P.MAINTENANCE_EXPORT,
    },

    # ── 4. Inventory Manager ──────────────────────────────────────────────────
    'inventory_manager': {
        P.LOCATIONS_VIEW,

        P.EMPLOYEES_VIEW,

        P.LOOKUPS_VIEW, P.LOOKUPS_CREATE, P.LOOKUPS_EDIT, P.LOOKUPS_DELETE,

        P.DEVICES_VIEW, P.DEVICES_CREATE, P.DEVICES_EDIT, P.DEVICES_DELETE,
        P.DEVICES_VIEW_SPECS, P.DEVICES_RETIRE, P.DEVICES_CHANGE_FLAG,
        P.DEVICES_EXPORT, P.DEVICES_VIEW_HISTORY,

        P.ACCESSORIES_VIEW, P.ACCESSORIES_CREATE, P.ACCESSORIES_EDIT,
        P.ACCESSORIES_DELETE, P.ACCESSORIES_LINK_DEVICE,

        P.ASSIGNMENTS_VIEW, P.ASSIGNMENTS_EXPORT,

        P.TRANSFERS_VIEW,

        P.MAINTENANCE_VIEW,
    },

    # ── 5. Site Manager ───────────────────────────────────────────────────────
    'site_manager': {
        P.LOCATIONS_VIEW,

        P.EMPLOYEES_VIEW, P.EMPLOYEES_CREATE,
        P.EMPLOYEES_EDIT, P.EMPLOYEES_TRANSFER,

        P.LOOKUPS_VIEW,

        P.DEVICES_VIEW, P.DEVICES_VIEW_SPECS, P.DEVICES_VIEW_HISTORY,

        P.ACCESSORIES_VIEW, P.ACCESSORIES_LINK_DEVICE,

        P.ASSIGNMENTS_VIEW, P.ASSIGNMENTS_CREATE, P.ASSIGNMENTS_EDIT,
        P.ASSIGNMENTS_RETURN, P.ASSIGNMENTS_EXPORT,

        P.TRANSFERS_VIEW, P.TRANSFERS_CREATE,

        P.MAINTENANCE_VIEW,
    },

    # ── 6. Maintenance Technician ─────────────────────────────────────────────
    'maintenance_tech': {
        P.LOCATIONS_VIEW,

        P.LOOKUPS_VIEW,

        P.DEVICES_VIEW, P.DEVICES_VIEW_SPECS, P.DEVICES_TOGGLE_MAINTENANCE,

        P.ACCESSORIES_VIEW,

        P.ASSIGNMENTS_VIEW,

        P.TRANSFERS_VIEW,

        P.MAINTENANCE_VIEW, P.MAINTENANCE_CREATE, P.MAINTENANCE_EDIT,
        P.MAINTENANCE_CLOSE, P.MAINTENANCE_EXPORT,
    },

    # ── 7. Auditor ────────────────────────────────────────────────────────────
    'auditor': {
        P.USERS_VIEW,

        P.LOCATIONS_VIEW,

        P.EMPLOYEES_VIEW,

        P.LOOKUPS_VIEW,

        P.DEVICES_VIEW, P.DEVICES_VIEW_SPECS,
        P.DEVICES_EXPORT, P.DEVICES_VIEW_HISTORY,

        P.ACCESSORIES_VIEW,

        P.ASSIGNMENTS_VIEW, P.ASSIGNMENTS_EXPORT,

        P.TRANSFERS_VIEW,

        P.MAINTENANCE_VIEW, P.MAINTENANCE_VIEW_COST, P.MAINTENANCE_EXPORT,
    },

    # ── 8. Viewer ─────────────────────────────────────────────────────────────
    'viewer': {
        P.LOCATIONS_VIEW,
        P.EMPLOYEES_VIEW,
        P.LOOKUPS_VIEW,
        P.DEVICES_VIEW,
        P.ACCESSORIES_VIEW,
        P.ASSIGNMENTS_VIEW,
        P.TRANSFERS_VIEW,
        P.MAINTENANCE_VIEW,
    },
}


# ══════════════════════════════════════════════════════════════════════════════
# SITE SCOPE
# ══════════════════════════════════════════════════════════════════════════════
#
# 'all'  → user sees records from every branch
# 'own'  → user sees records from their assigned site only
#
# Special cases (always override the role scope):
#   - user.site is NULL  → sees all branches regardless of role
#   - unauthenticated    → sees nothing
#
# To change a role's scope, just swap 'own' ↔ 'all' below.
# ─────────────────────────────────────────────────────────────────────────────

ROLE_SITE_SCOPE = {
    'super_admin':       'all',
    'it_admin':          'all',
    'it_supervisor':     'all',
    'auditor':           'all',
    'inventory_manager': 'all',
    'site_manager':      'own',
    'maintenance_tech':  'own',
    'viewer':            'own',
}


def get_site_filter(user, prefix=''):
    """
    Returns a dict to unpack into a queryset .filter() call.

    Parameters
    ──────────
    user    : the request.user
    prefix  : dot-path to the `site` field when it's not direct on the model.
              e.g. 'device__'  →  filters on  device__site=...
                   'employee__' →  filters on  employee__site=...

    Examples
    ────────
    # Model has a direct `site` FK  (Device, Accessory, Employee …)
    Device.objects.filter(**get_site_filter(request.user))

    # Model reaches site via a related field  (DeviceAssignment, MaintenanceRecord …)
    DeviceAssignment.objects.filter(**get_site_filter(request.user, prefix='device__'))
    MaintenanceRecord.objects.filter(**get_site_filter(request.user, prefix='device__'))

    Return values
    ─────────────
    {}                          → no filter applied  (sees all)
    {'site': <Site obj>}        → filtered to user's site
    {'site_id': None}           → safety fallback for unauthenticated users
                                  (returns empty queryset)
    """
    if not user or not user.is_authenticated:
        # Safety: unauthenticated callers should never reach a view,
        # but if they do, return nothing.
        return {f'{prefix}site_id': None}

    # NULL site → global access regardless of role
    if not user.site_id:
        return {}

    role  = getattr(user, 'role', 'viewer')
    scope = ROLE_SITE_SCOPE.get(role, 'own')

    if scope == 'all':
        return {}

    return {f'{prefix}site': user.site}


def sees_all_sites(user):
    """
    Returns True if the user can see records from all branches.

    Use this in views / templates to decide whether to show a
    branch selector / filter dropdown.

    Template usage (via context_processors):
        {% if rbac.sees_all_sites %}
            <select name="site">...</select>
        {% endif %}
    """
    if not user or not user.is_authenticated:
        return False
    if not user.site_id:
        return True
    role  = getattr(user, 'role', 'viewer')
    scope = ROLE_SITE_SCOPE.get(role, 'own')
    return scope == 'all'


# ══════════════════════════════════════════════════════════════════════════════
# CORE HELPER
# ══════════════════════════════════════════════════════════════════════════════

def has_permission(user, perm):
    """
    Return True if the user holds the given permission string.

    Logic
    ─────
    1. Unauthenticated → False
    2. Django superuser flag → True  (emergency hatch)
    3. Role == 'super_admin' → True
    4. ROLE_PERMISSIONS[role] is None → True  (None = full access sentinel)
    5. perm in role's permission set → True / False
    """
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    role = getattr(user, 'role', None)
    if not role:
        return False
    if role == 'super_admin':
        return True
    role_perms = ROLE_PERMISSIONS.get(role)
    if role_perms is None:
        return True
    return perm in role_perms


# ══════════════════════════════════════════════════════════════════════════════
# VIEW DECORATOR
# ══════════════════════════════════════════════════════════════════════════════

def permission_required(perm):
    """
    Gate a view behind a single Perms constant.

    AJAX requests (X-Requested-With: XMLHttpRequest) receive a 403 JSON.
    Regular requests are redirected to 'dashboard' with an error message.

    Usage
    ─────
      @permission_required(Perms.DEVICES_CREATE)
      def add_device(request): ...
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            if not has_permission(request.user, perm):
                is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
                if is_ajax:
                    return JsonResponse(
                        {'success': False, 'message': 'Permission denied.'}, status=403
                    )
                messages.error(request, 'You do not have permission to perform this action.')
                return redirect('dashboard')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator