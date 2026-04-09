"""
accounts/models.py
──────────────────
Role is stored as a CharField directly on User.
All permission logic lives in accounts/permissions.py.
"""

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class UserManager(BaseUserManager):

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user  = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff',     True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role',         'super_admin')
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    System user.  Role drives every RBAC decision — see permissions.py.

    Roles (least → most privileged)
    ────────────────────────────────
      viewer            Read-only on non-sensitive data
      maintenance_tech  Maintenance records + device view
      site_manager      Assignment management at their site
      inventory_manager Full device/accessory/lookup CRUD
      it_supervisor     Oversight: approvals, reports, cost view
      auditor           Read-only on EVERYTHING including costs
      it_admin          Full CRUD everywhere — no role assignment
      super_admin       Unrestricted
    """

    # ── Role constants ────────────────────────────────────────────────────────
    SUPER_ADMIN       = 'super_admin'
    IT_ADMIN          = 'it_admin'
    IT_SUPERVISOR     = 'it_supervisor'
    INVENTORY_MANAGER = 'inventory_manager'
    SITE_MANAGER      = 'site_manager'
    MAINTENANCE_TECH  = 'maintenance_tech'
    AUDITOR           = 'auditor'
    VIEWER            = 'viewer'

    ROLE_CHOICES = [
        (SUPER_ADMIN,       'Super Administrator'),
        (IT_ADMIN,          'IT Admin'),
        (IT_SUPERVISOR,     'IT Supervisor'),
        (INVENTORY_MANAGER, 'Inventory Manager'),
        (SITE_MANAGER,      'Site Manager'),
        (MAINTENANCE_TECH,  'Maintenance Technician'),
        (AUDITOR,           'Auditor'),
        (VIEWER,            'Viewer'),
    ]

    # Bootstrap / Tailwind colour token used in templates: {{ rbac.role_color }}
    ROLE_COLORS = {
        SUPER_ADMIN:       'danger',
        IT_ADMIN:          'primary',
        IT_SUPERVISOR:     'info',
        INVENTORY_MANAGER: 'purple',
        SITE_MANAGER:      'warning',
        MAINTENANCE_TECH:  'success',
        AUDITOR:           'dark',
        VIEWER:            'secondary',
    }

    # ── Fields ────────────────────────────────────────────────────────────────
    first_name = models.CharField(max_length=255)
    last_name  = models.CharField(max_length=255)
    email      = models.EmailField(max_length=255, unique=True)
    role       = models.CharField(max_length=30, choices=ROLE_CHOICES, default=VIEWER)

    site = models.ForeignKey(
        'locations.Site',
        on_delete=models.PROTECT,
        related_name='users',
        null=True, blank=True,
    )

    is_active = models.BooleanField(default=True)
    is_staff  = models.BooleanField(default=False)

    created_by   = models.ForeignKey(
        'self', on_delete=models.PROTECT,
        related_name='created_users',
        null=True, blank=True,
        db_column='Created_By',
    )
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True, null=True, blank=True)
    deleted_date = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        db_table = 'Users'

    def __str__(self):
        return f'{self.first_name} {self.last_name}'

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    @property
    def role_color(self):
        return self.ROLE_COLORS.get(self.role, 'secondary')