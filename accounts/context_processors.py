"""
accounts/context_processors.py
───────────────────────────────
Injects an `rbac` dict into every template so you can gate UI elements
without any extra view logic.

Template usage
──────────────
  {% if rbac.devices_create %}
      <a href="{% url 'device-add' %}">Add device</a>
  {% endif %}

  {% if rbac.maintenance_view_cost %}
      <td>{{ record.cost }}</td>
  {% endif %}

  {% if rbac.sees_all_sites %}
      <select name="site">...</select>   {# branch selector shown only to global roles #}
  {% endif %}

  <span class="badge bg-{{ rbac.role_color }}">{{ rbac.role_display }}</span>

Register in settings.py:
    TEMPLATES[0]['OPTIONS']['context_processors'] += [
        'accounts.context_processors.user_permissions',
    ]
"""

from .permissions import has_permission, sees_all_sites, Perms


def user_permissions(request):
    if not request.user.is_authenticated:
        return {'rbac': {}}

    hp = lambda p: has_permission(request.user, p)

    rbac = {
        # ── Users ─────────────────────────────────────────────────────────────
        'users_view':           hp(Perms.USERS_VIEW),
        'users_create':         hp(Perms.USERS_CREATE),
        'users_edit':           hp(Perms.USERS_EDIT),
        'users_delete':         hp(Perms.USERS_DELETE),
        'users_assign_role':    hp(Perms.USERS_ASSIGN_ROLE),
        'users_reset_password': hp(Perms.USERS_RESET_PASSWORD),
        'users_activate':       hp(Perms.USERS_ACTIVATE),

        # ── Locations ─────────────────────────────────────────────────────────
        'locations_view':   hp(Perms.LOCATIONS_VIEW),
        'locations_create': hp(Perms.LOCATIONS_CREATE),
        'locations_edit':   hp(Perms.LOCATIONS_EDIT),
        'locations_delete': hp(Perms.LOCATIONS_DELETE),

        # ── Employees ─────────────────────────────────────────────────────────
        'employees_view':     hp(Perms.EMPLOYEES_VIEW),
        'employees_create':   hp(Perms.EMPLOYEES_CREATE),
        'employees_edit':     hp(Perms.EMPLOYEES_EDIT),
        'employees_delete':   hp(Perms.EMPLOYEES_DELETE),
        'employees_transfer': hp(Perms.EMPLOYEES_TRANSFER),

        # ── Lookup tables ─────────────────────────────────────────────────────
        'lookups_view':   hp(Perms.LOOKUPS_VIEW),
        'lookups_create': hp(Perms.LOOKUPS_CREATE),
        'lookups_edit':   hp(Perms.LOOKUPS_EDIT),
        'lookups_delete': hp(Perms.LOOKUPS_DELETE),

        # ── Devices ───────────────────────────────────────────────────────────
        'devices_view':               hp(Perms.DEVICES_VIEW),
        'devices_create':             hp(Perms.DEVICES_CREATE),
        'devices_edit':               hp(Perms.DEVICES_EDIT),
        'devices_delete':             hp(Perms.DEVICES_DELETE),
        'devices_view_specs':         hp(Perms.DEVICES_VIEW_SPECS),
        'devices_retire':             hp(Perms.DEVICES_RETIRE),
        'devices_change_flag':        hp(Perms.DEVICES_CHANGE_FLAG),
        'devices_toggle_maintenance': hp(Perms.DEVICES_TOGGLE_MAINTENANCE),
        'devices_export':             hp(Perms.DEVICES_EXPORT),
        'devices_view_history':       hp(Perms.DEVICES_VIEW_HISTORY),

        # ── Accessories ───────────────────────────────────────────────────────
        'accessories_view':        hp(Perms.ACCESSORIES_VIEW),
        'accessories_create':      hp(Perms.ACCESSORIES_CREATE),
        'accessories_edit':        hp(Perms.ACCESSORIES_EDIT),
        'accessories_delete':      hp(Perms.ACCESSORIES_DELETE),
        'accessories_link_device': hp(Perms.ACCESSORIES_LINK_DEVICE),

        # ── Assignments ───────────────────────────────────────────────────────
        'assignments_view':   hp(Perms.ASSIGNMENTS_VIEW),
        'assignments_create': hp(Perms.ASSIGNMENTS_CREATE),
        'assignments_edit':   hp(Perms.ASSIGNMENTS_EDIT),
        'assignments_delete': hp(Perms.ASSIGNMENTS_DELETE),
        'assignments_return': hp(Perms.ASSIGNMENTS_RETURN),
        'assignments_export': hp(Perms.ASSIGNMENTS_EXPORT),

        # ── Transfers ─────────────────────────────────────────────────────────
        'transfers_view':    hp(Perms.TRANSFERS_VIEW),
        'transfers_create':  hp(Perms.TRANSFERS_CREATE),
        'transfers_approve': hp(Perms.TRANSFERS_APPROVE),
        'transfers_delete':  hp(Perms.TRANSFERS_DELETE),

        # ── Maintenance ───────────────────────────────────────────────────────
        'maintenance_view':      hp(Perms.MAINTENANCE_VIEW),
        'maintenance_create':    hp(Perms.MAINTENANCE_CREATE),
        'maintenance_edit':      hp(Perms.MAINTENANCE_EDIT),
        'maintenance_delete':    hp(Perms.MAINTENANCE_DELETE),
        'maintenance_close':     hp(Perms.MAINTENANCE_CLOSE),
        'maintenance_view_cost': hp(Perms.MAINTENANCE_VIEW_COST),
        'maintenance_export':    hp(Perms.MAINTENANCE_EXPORT),

        # ── Site scope ────────────────────────────────────────────────────────
        # True  → user can see all branches (show branch selector in UI)
        # False → user is locked to their own branch only
        'sees_all_sites': sees_all_sites(request.user),
    }

    # ── Role metadata ─────────────────────────────────────────────────────────
    rbac['role']         = getattr(request.user, 'role', 'viewer')
    rbac['role_display'] = (request.user.get_role_display()
                            if hasattr(request.user, 'get_role_display') else '')
    rbac['role_color']   = getattr(request.user, 'role_color', 'secondary')

    return {'rbac': rbac}