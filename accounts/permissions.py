"""
accounts/permissions.py
───────────────────────
42 permissions across 8 roles covering every model and action in the system.

Quick reference
───────────────
  from accounts.permissions import has_permission, permission_required, Perms

  # guard a view
  @permission_required(Perms.DEVICES_CREATE)
  def add_device(request): ...

  # guard a code path
  if has_permission(request.user, Perms.MAINTENANCE_VIEW_COST):
      ...

  # templates — injected automatically by context_processors.py
  {% if rbac.devices_create %} ... {% endif %}
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
    USERS_ASSIGN_ROLE        = 'users.assign_role'         # change another user's role
    USERS_RESET_PASSWORD     = 'users.reset_password'      # force-reset a user's password
    USERS_ACTIVATE           = 'users.activate'            # activate / deactivate accounts

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
    EMPLOYEES_TRANSFER       = 'employees.transfer'        # move employee to another site/dept

    # ── Lookup tables — Brand, Category, Model, CPU, GPU, OS, Flag,
    #                    AccessoryType  (4) ─────────────────────────────────────
    LOOKUPS_VIEW             = 'lookups.view'
    LOOKUPS_CREATE           = 'lookups.create'
    LOOKUPS_EDIT             = 'lookups.edit'
    LOOKUPS_DELETE           = 'lookups.delete'

    # ── Devices (10) ──────────────────────────────────────────────────────────
    DEVICES_VIEW             = 'devices.view'
    DEVICES_CREATE           = 'devices.create'
    DEVICES_EDIT             = 'devices.edit'
    DEVICES_DELETE           = 'devices.delete'
    DEVICES_VIEW_SPECS       = 'devices.view_specs'        # CPU/GPU/RAM/storage/OS fields
    DEVICES_RETIRE           = 'devices.retire'            # set flag → Retired
    DEVICES_CHANGE_FLAG      = 'devices.change_flag'       # set flag to any value
    DEVICES_TOGGLE_MAINTENANCE = 'devices.toggle_maintenance'  # set/clear maintenance_mode
    DEVICES_EXPORT           = 'devices.export'            # download CSV / PDF list
    DEVICES_VIEW_HISTORY     = 'devices.view_history'      # DeliveredDeviceHistory

    # ── Accessories (5) ───────────────────────────────────────────────────────
    ACCESSORIES_VIEW         = 'accessories.view'
    ACCESSORIES_CREATE       = 'accessories.create'
    ACCESSORIES_EDIT         = 'accessories.edit'
    ACCESSORIES_DELETE       = 'accessories.delete'
    ACCESSORIES_LINK_DEVICE  = 'accessories.link_device'   # attach/detach from a device

    # ── Assignments (6) ───────────────────────────────────────────────────────
    ASSIGNMENTS_VIEW         = 'assignments.view'
    ASSIGNMENTS_CREATE       = 'assignments.create'        # assign device to employee
    ASSIGNMENTS_EDIT         = 'assignments.edit'          # edit notes on an assignment
    ASSIGNMENTS_DELETE       = 'assignments.delete'
    ASSIGNMENTS_RETURN       = 'assignments.return'        # record device returned
    ASSIGNMENTS_EXPORT       = 'assignments.export'        # download assignment report

    # ── Transfers (4) ─────────────────────────────────────────────────────────
    TRANSFERS_VIEW           = 'transfers.view'
    TRANSFERS_CREATE         = 'transfers.create'          # initiate a site transfer
    TRANSFERS_APPROVE        = 'transfers.approve'         # approve a pending transfer
    TRANSFERS_DELETE         = 'transfers.delete'

    # ── Maintenance (7) ───────────────────────────────────────────────────────
    MAINTENANCE_VIEW         = 'maintenance.view'
    MAINTENANCE_CREATE       = 'maintenance.create'
    MAINTENANCE_EDIT         = 'maintenance.edit'
    MAINTENANCE_DELETE       = 'maintenance.delete'
    MAINTENANCE_CLOSE        = 'maintenance.close'         # set returned_date + resolution
    MAINTENANCE_VIEW_COST    = 'maintenance.view_cost'     # sensitive financial field
    MAINTENANCE_EXPORT       = 'maintenance.export'        # download maintenance report

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

P = Perms  # alias for readable set literals below

ROLE_PERMISSIONS = {

    # ── 1. Super Admin ────────────────────────────────────────────────────────
    # None = skip the set check → always True
    'super_admin': None,

    # ── 2. IT Admin ───────────────────────────────────────────────────────────
    # Full CRUD on everything. Cannot assign roles (that's super_admin only).
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
    # Oversight role: approves, closes, exports, views costs.
    # Can manage day-to-day assignments and maintenance but cannot add/delete devices.
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
    # Owns the asset registry: full CRUD on devices, accessories, and all
    # lookup tables. Views assignments and maintenance but doesn't manage them.
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
    # Manages everything at their physical site: assigns and returns devices,
    # transfers devices, manages local employees. Cannot add or delete devices.
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
    # Creates and manages maintenance records. Can toggle maintenance mode on
    # devices and see full hardware specs. No assignment or user access.
    'maintenance_tech': {
        P.LOCATIONS_VIEW,

        P.LOOKUPS_VIEW,

        P.DEVICES_VIEW, P.DEVICES_VIEW_SPECS, P.DEVICES_TOGGLE_MAINTENANCE,

        P.ACCESSORIES_VIEW,

        P.ASSIGNMENTS_VIEW,

        P.TRANSFERS_VIEW,

        P.MAINTENANCE_VIEW, P.MAINTENANCE_CREATE, P.MAINTENANCE_EDIT,
        P.MAINTENANCE_CLOSE, P.MAINTENANCE_EXPORT,
        # NOTE: MAINTENANCE_VIEW_COST is intentionally excluded —
        # financial data is restricted to supervisor / admin roles.
    },

    # ── 7. Auditor ────────────────────────────────────────────────────────────
    # Read-only on EVERYTHING, including costs, specs, and user list.
    # Cannot modify anything. Designed for compliance / audit use.
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
    # Basic read-only. No costs, no hardware specs, no user list.
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
    if role_perms is None:          # None sentinel → full access
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