"""
accounts/permissions.py
───────────────────────
Thin bridge between the app's permission constants and Django's built-in
per-user permission system.

Every Perms constant is now a real Django permission codename in the form
'app_label.codename'.  has_permission() delegates to user.has_perm(), so
Django handles superusers, group membership, and per-user grants automatically.

Quick reference
───────────────
  from accounts.permissions import has_permission, permission_required, Perms

  # guard a view
  @permission_required(Perms.DEVICES_CREATE)
  def add_device(request): ...

  # guard a code path
  if has_permission(request.user, Perms.MAINTENANCE_VIEW_COST):
      ...

  # site-scoped queryset — works on any model with a direct `site` FK
  devices = Device.objects.filter(site__in=request.user.get_allowed_sites())

  # site-scoped queryset — model with indirect site (via related field)
  assignments = DeviceAssignment.objects.filter(
      device__site__in=request.user.get_allowed_sites()
  )

  # templates — injected automatically by context_processors.py
  {% if rbac.devices_create %} ... {% endif %}
  {% if rbac.site_scope == 'all' %} ... {% endif %}
"""

from functools import wraps
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect


# ══════════════════════════════════════════════════════════════════════════════
# PERMISSION CONSTANTS  (Django codenames: 'app_label.codename')
# ══════════════════════════════════════════════════════════════════════════════

class Perms:

    # ── Users / Accounts ──────────────────────────────────────────────────────
    USERS_VIEW           = 'accounts.view_user'
    USERS_CREATE         = 'accounts.add_user'
    USERS_EDIT           = 'accounts.change_user'
    USERS_DELETE         = 'accounts.delete_user'
    USERS_RESET_PASSWORD = 'accounts.reset_password_user'
    USERS_ACTIVATE       = 'accounts.activate_user'

    # ── Locations — Sites + Governorates ─────────────────────────────────────
    # A single check on the Site model gates both Site and Governorate views.
    LOCATIONS_VIEW           = 'locations.view_site'
    LOCATIONS_CREATE         = 'locations.add_site'
    LOCATIONS_EDIT           = 'locations.change_site'
    LOCATIONS_DELETE         = 'locations.delete_site'

    # ── Employees + Departments ───────────────────────────────────────────────
    EMPLOYEES_VIEW           = 'employees.view_employee'
    EMPLOYEES_CREATE         = 'employees.add_employee'
    EMPLOYEES_EDIT           = 'employees.change_employee'
    EMPLOYEES_DELETE         = 'employees.delete_employee'
    EMPLOYEES_TRANSFER       = 'employees.transfer_employee'

    # ── Lookup tables ─────────────────────────────────────────────────────────
    # DeviceCategory is the representative model; one check gates all lookups
    # (Brand, DeviceModel, CPU, GPU, OperatingSystem, AccessoryType).
    LOOKUPS_VIEW             = 'inventory.view_devicecategory'
    LOOKUPS_CREATE           = 'inventory.add_devicecategory'
    LOOKUPS_EDIT             = 'inventory.change_devicecategory'
    LOOKUPS_DELETE           = 'inventory.delete_devicecategory'

    # ── Devices ───────────────────────────────────────────────────────────────
    DEVICES_VIEW               = 'inventory.view_device'
    DEVICES_CREATE             = 'inventory.add_device'
    DEVICES_EDIT               = 'inventory.change_device'
    DEVICES_DELETE             = 'inventory.delete_device'
    DEVICES_VIEW_SPECS         = 'inventory.view_device_specs'
    DEVICES_RETIRE             = 'inventory.retire_device'
    DEVICES_CHANGE_FLAG        = 'inventory.flag_device'
    DEVICES_TOGGLE_MAINTENANCE = 'inventory.toggle_maintenance'
    DEVICES_EXPORT             = 'inventory.export_device'
    DEVICES_VIEW_HISTORY       = 'inventory.view_history_device'

    # ── Accessories ───────────────────────────────────────────────────────────
    ACCESSORIES_VIEW         = 'inventory.view_accessory'
    ACCESSORIES_CREATE       = 'inventory.add_accessory'
    ACCESSORIES_EDIT         = 'inventory.change_accessory'
    ACCESSORIES_DELETE       = 'inventory.delete_accessory'
    ACCESSORIES_LINK_DEVICE  = 'inventory.link_device_accessory'

    # ── Assignments ───────────────────────────────────────────────────────────
    ASSIGNMENTS_VIEW         = 'assignments.view_deviceassignment'
    ASSIGNMENTS_CREATE       = 'assignments.add_deviceassignment'
    ASSIGNMENTS_EDIT         = 'assignments.change_deviceassignment'
    ASSIGNMENTS_DELETE       = 'assignments.delete_deviceassignment'
    ASSIGNMENTS_RETURN       = 'assignments.return_device'
    ASSIGNMENTS_EXPORT       = 'assignments.generate_report'

    # ── Transfers ─────────────────────────────────────────────────────────────
    TRANSFERS_VIEW           = 'assignments.view_devicetransfer'
    TRANSFERS_CREATE         = 'assignments.add_devicetransfer'
    TRANSFERS_APPROVE        = 'assignments.approve_transfer'
    TRANSFERS_DELETE         = 'assignments.delete_devicetransfer'

    # ── Maintenance ───────────────────────────────────────────────────────────
    MAINTENANCE_VIEW         = 'maintenance.view_maintenancerecord'
    MAINTENANCE_CREATE       = 'maintenance.add_maintenancerecord'
    MAINTENANCE_EDIT         = 'maintenance.change_maintenancerecord'
    MAINTENANCE_DELETE       = 'maintenance.delete_maintenancerecord'
    MAINTENANCE_CLOSE        = 'maintenance.close_maintenancerecord'
    MAINTENANCE_VIEW_COST    = 'maintenance.view_cost'
    MAINTENANCE_EXPORT       = 'maintenance.export_maintenancerecord'

    ALL = [
        USERS_VIEW, USERS_CREATE, USERS_EDIT, USERS_DELETE,
        USERS_RESET_PASSWORD, USERS_ACTIVATE,

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
# CORE HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def has_permission(user, perm):
    """
    Return True if the user holds the given Django permission codename.

    Delegates entirely to user.has_perm() — Django handles:
      • is_superuser → always True
      • user.user_permissions (per-user grants)
      • user.groups (group-based grants)
    """
    if not user or not user.is_authenticated:
        return False
    return user.has_perm(perm)


def get_site_filter(user, prefix=''):
    """
    Returns a dict to unpack into a queryset .filter() call,
    scoped to the sites the user is allowed to see.

    Kept for backward compatibility with views not yet migrated to
    .filter(site__in=request.user.get_allowed_sites()).

    Parameters
    ──────────
    user    : the request.user
    prefix  : relationship path to the `site` FK when it's not direct.
              e.g. 'device__'  → filters on  device__site__in=...
                   'employee__' → filters on  employee__site__in=...

    Examples
    ────────
    Device.objects.filter(**get_site_filter(request.user))
    DeviceAssignment.objects.filter(**get_site_filter(request.user, prefix='device__'))
    """
    if not user or not user.is_authenticated:
        return {f'{prefix}site_id': None}

    allowed = user.get_allowed_sites()

    # get_allowed_sites() returns Site.objects.all() for global users — no filter needed.
    # We detect this by checking if it's an "all sites" scope.
    from accounts.models import User as _User
    if user.is_superuser or getattr(user, 'site_scope', _User.SiteScope.OWN) == _User.SiteScope.ALL:
        return {}

    return {f'{prefix}site__in': allowed}


def sees_all_sites(user):
    """
    Returns True if the user can see records from all branches.
    Used in the context processor to populate rbac.sees_all_sites.
    """
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    from accounts.models import User as _User
    return getattr(user, 'site_scope', _User.SiteScope.OWN) == _User.SiteScope.ALL


# ══════════════════════════════════════════════════════════════════════════════
# VIEW DECORATOR
# ══════════════════════════════════════════════════════════════════════════════

def permission_required(perm):
    """
    Gate a view behind a single Perms constant (Django codename).

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
