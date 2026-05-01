"""
accounts/management/commands/convert_role_permissions.py
──────────────────────────────────────────────────────────
One-time migration command: converts the old static role-based permission
system to Django's per-user permission grants.

For every active, non-deleted user:
  • super_admin  → is_superuser = True  (bypass all permission checks)
  • all others   → user.user_permissions.set( <Django Permission objects
                   matching the old ROLE_PERMISSIONS set> )

Run once after deploying the new permission system:

    python manage.py convert_role_permissions

Use --dry-run to preview changes without saving anything.
Use --role <role>  to process only users with that role.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Permission


# ── Old role → Perms constant mapping (copied verbatim from the old system) ──
# Keeping this here makes the command self-contained and not dependent on the
# current permissions.py state.

_P = {
    # Users
    'users_view':               'accounts.view_user',
    'users_create':             'accounts.add_user',
    'users_edit':               'accounts.change_user',
    'users_delete':             'accounts.delete_user',
    'users_assign_role':        'accounts.assign_role_user',
    'users_reset_password':     'accounts.reset_password_user',
    'users_activate':           'accounts.activate_user',
    # Locations
    'locations_view':           'locations.view_site',
    'locations_create':         'locations.add_site',
    'locations_edit':           'locations.change_site',
    'locations_delete':         'locations.delete_site',
    # Employees
    'employees_view':           'employees.view_employee',
    'employees_create':         'employees.add_employee',
    'employees_edit':           'employees.change_employee',
    'employees_delete':         'employees.delete_employee',
    'employees_transfer':       'employees.transfer_employee',
    # Lookups
    'lookups_view':             'inventory.view_devicecategory',
    'lookups_create':           'inventory.add_devicecategory',
    'lookups_edit':             'inventory.change_devicecategory',
    'lookups_delete':           'inventory.delete_devicecategory',
    # Devices
    'devices_view':             'inventory.view_device',
    'devices_create':           'inventory.add_device',
    'devices_edit':             'inventory.change_device',
    'devices_delete':           'inventory.delete_device',
    'devices_view_specs':       'inventory.view_device_specs',
    'devices_retire':           'inventory.retire_device',
    'devices_change_flag':      'inventory.flag_device',
    'devices_toggle_maintenance': 'inventory.toggle_maintenance',
    'devices_export':           'inventory.export_device',
    'devices_view_history':     'inventory.view_history_device',
    # Accessories
    'accessories_view':         'inventory.view_accessory',
    'accessories_create':       'inventory.add_accessory',
    'accessories_edit':         'inventory.change_accessory',
    'accessories_delete':       'inventory.delete_accessory',
    'accessories_link_device':  'inventory.link_device_accessory',
    # Assignments
    'assignments_view':         'assignments.view_deviceassignment',
    'assignments_create':       'assignments.add_deviceassignment',
    'assignments_edit':         'assignments.change_deviceassignment',
    'assignments_delete':       'assignments.delete_deviceassignment',
    'assignments_return':       'assignments.return_device',
    'assignments_export':       'assignments.generate_report',
    # Transfers
    'transfers_view':           'assignments.view_devicetransfer',
    'transfers_create':         'assignments.add_devicetransfer',
    'transfers_approve':        'assignments.approve_transfer',
    'transfers_delete':         'assignments.delete_devicetransfer',
    # Maintenance
    'maintenance_view':         'maintenance.view_maintenancerecord',
    'maintenance_create':       'maintenance.add_maintenancerecord',
    'maintenance_edit':         'maintenance.change_maintenancerecord',
    'maintenance_delete':       'maintenance.delete_maintenancerecord',
    'maintenance_close':        'maintenance.close_maintenancerecord',
    'maintenance_view_cost':    'maintenance.view_cost',
    'maintenance_export':       'maintenance.export_maintenancerecord',
}

# Old role → set of permission keys from _P above (mirrors old ROLE_PERMISSIONS).
ROLE_PERMISSIONS = {
    'super_admin': None,   # None = superuser flag
    'it_admin': {
        'users_view', 'users_create', 'users_edit', 'users_delete',
        'users_reset_password', 'users_activate',
        'locations_view', 'locations_create', 'locations_edit', 'locations_delete',
        'employees_view', 'employees_create', 'employees_edit', 'employees_delete', 'employees_transfer',
        'lookups_view', 'lookups_create', 'lookups_edit', 'lookups_delete',
        'devices_view', 'devices_create', 'devices_edit', 'devices_delete',
        'devices_view_specs', 'devices_retire', 'devices_change_flag',
        'devices_toggle_maintenance', 'devices_export', 'devices_view_history',
        'accessories_view', 'accessories_create', 'accessories_edit', 'accessories_delete', 'accessories_link_device',
        'assignments_view', 'assignments_create', 'assignments_edit', 'assignments_delete', 'assignments_return', 'assignments_export',
        'transfers_view', 'transfers_create', 'transfers_approve', 'transfers_delete',
        'maintenance_view', 'maintenance_create', 'maintenance_edit', 'maintenance_delete',
        'maintenance_close', 'maintenance_view_cost', 'maintenance_export',
    },
    'it_supervisor': {
        'users_view',
        'locations_view',
        'employees_view', 'employees_transfer',
        'lookups_view',
        'devices_view', 'devices_view_specs', 'devices_change_flag', 'devices_toggle_maintenance', 'devices_export', 'devices_view_history',
        'accessories_view',
        'assignments_view', 'assignments_create', 'assignments_edit', 'assignments_return', 'assignments_export',
        'transfers_view', 'transfers_approve',
        'maintenance_view', 'maintenance_edit', 'maintenance_close', 'maintenance_view_cost', 'maintenance_export',
    },
    'inventory_manager': {
        'locations_view',
        'employees_view',
        'lookups_view', 'lookups_create', 'lookups_edit', 'lookups_delete',
        'devices_view', 'devices_create', 'devices_edit', 'devices_delete',
        'devices_view_specs', 'devices_retire', 'devices_change_flag', 'devices_export', 'devices_view_history',
        'accessories_view', 'accessories_create', 'accessories_edit', 'accessories_delete', 'accessories_link_device',
        'assignments_view', 'assignments_export',
        'transfers_view',
        'maintenance_view',
    },
    'site_manager': {
        'locations_view',
        'employees_view', 'employees_create', 'employees_edit', 'employees_transfer',
        'lookups_view',
        'devices_view', 'devices_view_specs', 'devices_view_history',
        'accessories_view', 'accessories_link_device',
        'assignments_view', 'assignments_create', 'assignments_edit', 'assignments_return', 'assignments_export',
        'transfers_view', 'transfers_create',
        'maintenance_view',
    },
    'maintenance_tech': {
        'locations_view',
        'lookups_view',
        'devices_view', 'devices_view_specs', 'devices_toggle_maintenance',
        'accessories_view',
        'assignments_view',
        'transfers_view',
        'maintenance_view', 'maintenance_create', 'maintenance_edit', 'maintenance_close', 'maintenance_export',
    },
    'auditor': {
        'users_view',
        'locations_view',
        'employees_view',
        'lookups_view',
        'devices_view', 'devices_view_specs', 'devices_export', 'devices_view_history',
        'accessories_view',
        'assignments_view', 'assignments_export',
        'transfers_view',
        'maintenance_view', 'maintenance_view_cost', 'maintenance_export',
    },
    'viewer': {
        'locations_view',
        'employees_view',
        'lookups_view',
        'devices_view',
        'accessories_view',
        'assignments_view',
        'transfers_view',
        'maintenance_view',
    },
}

# Old role → site scope
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


def _build_perm_map():
    """Return dict: 'app_label.codename' → Permission object."""
    perms = {}
    for p in Permission.objects.select_related('content_type').all():
        key = f'{p.content_type.app_label}.{p.codename}'
        perms[key] = p
    return perms


class Command(BaseCommand):
    help = (
        'Convert old role-based permissions to per-user Django permission grants. '
        'Run once after deploying the new permission system.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Preview changes without saving anything.',
        )
        parser.add_argument(
            '--role', type=str, default=None,
            help='Process only users with this role (e.g. site_manager).',
        )

    def handle(self, *args, **options):
        from accounts.models import User

        dry_run  = options['dry_run']
        role_filter = options['role']

        perm_map = _build_perm_map()

        qs = User.objects.filter(deleted_date__isnull=True, is_active=True)
        if role_filter:
            qs = qs.filter(role=role_filter)

        self.stdout.write(f'Processing {qs.count()} user(s)...\n')

        converted = 0
        skipped   = 0

        for user in qs.select_related('site'):
            role = user.role
            role_perm_keys = ROLE_PERMISSIONS.get(role)
            scope = ROLE_SITE_SCOPE.get(role, 'own')

            # ── super_admin → is_superuser ────────────────────────────────────
            if role_perm_keys is None:
                self.stdout.write(
                    f'  {user.email} ({role}) -> is_superuser=True'
                    + (' [dry-run]' if dry_run else '')
                )
                if not dry_run:
                    User.objects.filter(pk=user.pk).update(is_superuser=True, is_staff=True)
                converted += 1
                continue

            # ── Resolve Django Permission objects ─────────────────────────────
            django_codenames = [_P[k] for k in role_perm_keys if k in _P]
            perm_objects = []
            missing = []
            for codename in django_codenames:
                p = perm_map.get(codename)
                if p:
                    perm_objects.append(p)
                else:
                    missing.append(codename)

            if missing:
                self.stderr.write(
                    f'  WARNING: {user.email} — could not find permissions: {missing}'
                )

            # ── Set site scope ────────────────────────────────────────────────
            self.stdout.write(
                f'  {user.email} ({role}) -> {len(perm_objects)} perms, scope={scope}'
                + (' [dry-run]' if dry_run else '')
            )

            if not dry_run:
                user.user_permissions.set(perm_objects)
                # Set site_scope; for 'own' scope, copy existing site to own_site
                from accounts.models import User as _User
                new_scope = scope
                update_fields = {'site_scope': new_scope}
                if new_scope == 'own' and user.site_id and not user.own_site_id:
                    update_fields['own_site_id'] = user.site_id
                User.objects.filter(pk=user.pk).update(**update_fields)

            converted += 1

        mode = '[DRY RUN] ' if dry_run else ''
        self.stdout.write(
            self.style.SUCCESS(
                f'\n{mode}Done. Converted {converted}, skipped {skipped} user(s).'
            )
        )
