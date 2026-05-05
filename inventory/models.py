"""
inventory/models.py
───────────────────
Models: DeviceCategory, Brand, DeviceModel, CPU, GPU, OperatingSystem,
        Flag, Device, DeviceSpec, AccessoryType, Accessory

RBAC permissions
────────────────
Auto-created by Django (add / change / delete / view) for every model below.

Custom permissions:
  inventory.retire_device         – mark a device as Retired
  inventory.flag_device           – change the Flag on a device
  inventory.toggle_maintenance    – set / clear Device.maintenance_mode
  inventory.view_device_specs     – see detailed hardware specs
"""

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


# ── Lookup tables ─────────────────────────────────────────────────────────────

class DeviceCategory(models.Model):
    """Desktop, Laptop, Printer, Monitor, Scanner, UPS, Switch, …"""
    name         = models.CharField(max_length=255, unique=True)
    created_by   = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='created_device_categories', db_column='Created_By',
    )
    updated_by   = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        related_name='updated_device_categories', null=True, blank=True,
    )
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True, null=True, blank=True)
    deleted_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'Devices_Categories'

    def __str__(self):
        return self.name


class Brand(models.Model):
    name         = models.CharField(max_length=255, unique=True)
    created_by   = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='created_brands', db_column='Created_By',
    )
    updated_by   = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        related_name='updated_brands', null=True, blank=True,
    )
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True, null=True, blank=True)
    deleted_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'Brands'

    def __str__(self):
        return self.name


class DeviceModel(models.Model):
    name     = models.CharField(max_length=255)
    brand    = models.ForeignKey(Brand, on_delete=models.PROTECT, related_name='device_models')
    category = models.ForeignKey(DeviceCategory, on_delete=models.PROTECT, related_name='device_models')
    created_by   = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='created_device_models', db_column='Created_By',
    )
    updated_by   = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        related_name='updated_device_models', null=True, blank=True,
    )
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True, null=True, blank=True)
    deleted_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table        = 'Devices_Models'
        unique_together = ('name', 'brand')

    def __str__(self):
        return f'{self.brand.name} – {self.name}'


class CPU(models.Model):
    name     = models.CharField(max_length=255, unique=True)
    brand    = models.ForeignKey(Brand, on_delete=models.PROTECT, related_name='cpus')
    created_by   = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='created_cpus', db_column='Created_By',
    )
    updated_by   = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        related_name='updated_cpus', null=True, blank=True,
    )
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True, null=True, blank=True)
    deleted_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'CPUs'

    def __str__(self):
        return self.name


class GPU(models.Model):
    name     = models.CharField(max_length=255, unique=True)
    brand    = models.ForeignKey(Brand, on_delete=models.PROTECT, related_name='gpus')
    created_by   = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='created_gpus', db_column='Created_By',
    )
    updated_by   = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        related_name='updated_gpus', null=True, blank=True,
    )
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True, null=True, blank=True)
    deleted_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'GPUs'

    def __str__(self):
        return self.name


class OperatingSystem(models.Model):
    name         = models.CharField(max_length=255, unique=True)
    created_by   = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='created_operating_systems', db_column='Created_By',
    )
    updated_by   = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        related_name='updated_operating_systems', null=True, blank=True,
    )
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True, null=True, blank=True)
    deleted_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'Operating_Systems'

    def __str__(self):
        return self.name


class DeviceFlag(models.TextChoices):
    AVAILABLE         = 'available',         _('Available')
    ASSIGNED          = 'assigned',          _('Assigned')
    LOST              = 'lost',              _('Lost')
    RETIRED           = 'retired',           _('Retired')
    UNDER_MAINTENANCE = 'under_maintenance', _('Under Maintenance')


# ── Core device ───────────────────────────────────────────────────────────────

class Device(models.Model):
    serial_number = models.CharField(max_length=255, unique=True)
    category      = models.ForeignKey(DeviceCategory, on_delete=models.PROTECT, related_name='devices')
    brand         = models.ForeignKey(Brand,          on_delete=models.PROTECT, related_name='devices')
    device_model  = models.ForeignKey(DeviceModel,    on_delete=models.PROTECT, related_name='devices')
    site          = models.ForeignKey('locations.Site', on_delete=models.PROTECT, related_name='devices')
    flag          = models.CharField(max_length=20, choices=DeviceFlag.choices, default=DeviceFlag.AVAILABLE)

    # ── Compute specs (desktops / laptops) ────────────────────────────────────
    cpu              = models.ForeignKey(CPU, on_delete=models.SET_NULL, null=True, blank=True, related_name='devices')
    gpu              = models.ForeignKey(GPU, on_delete=models.SET_NULL, null=True, blank=True, related_name='devices')
    ram_size_gb      = models.PositiveSmallIntegerField(null=True, blank=True, help_text='RAM in GB')
    hdd_storage_gb   = models.PositiveIntegerField(null=True, blank=True, help_text='HDD in GB')
    ssd_storage_gb   = models.PositiveIntegerField(null=True, blank=True, help_text='SSD in GB')
    operating_system = models.ForeignKey(OperatingSystem, on_delete=models.SET_NULL, null=True, blank=True, related_name='devices')

    # ── Display / peripheral specs ────────────────────────────────────────────
    screen_size_inch = models.FloatField(null=True, blank=True, help_text='Screen size in inches')
    ports_number     = models.PositiveSmallIntegerField(null=True, blank=True)

    # ── Status ────────────────────────────────────────────────────────────────
    maintenance_mode = models.BooleanField(default=False)
    notes            = models.TextField(null=True, blank=True)

    # ── Audit ─────────────────────────────────────────────────────────────────
    created_by   = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='created_devices', db_column='Created_By',
    )
    updated_by   = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        related_name='updated_devices', null=True, blank=True,
    )
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True, null=True, blank=True)
    deleted_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'Devices'
        permissions = [
            ('retire_device',       'Can mark a device as Retired'),
            ('flag_device',         'Can change the status flag of a device'),
            ('toggle_maintenance',  'Can toggle maintenance mode on a device'),
            ('view_device_specs',   'Can view detailed hardware specifications'),
            ('export_device',       'Can export device data to a file'),
            ('view_history_device', 'Can view the assignment history of a device'),
        ]

    def __str__(self):
        return f'{self.device_model} — {self.serial_number}'

    @property
    def is_available(self):
        return self.flag == DeviceFlag.AVAILABLE

    @property
    def current_assignment(self):
        return self.assignments.filter(returned_date__isnull=True).first()


class DeviceSpec(models.Model):
    """
    Flexible key-value specs per category.
    Monitor  → Resolution, Panel, Refresh Rate
    Printer  → Print Speed, Color
    Scanner  → DPI, Scan Type
    """
    device     = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='specs')
    spec_name  = models.CharField(max_length=100)
    spec_value = models.CharField(max_length=255)

    class Meta:
        db_table        = 'Device_Specs'
        unique_together = ('device', 'spec_name')

    def __str__(self):
        return f'{self.device.serial_number} | {self.spec_name}: {self.spec_value}'


# ── Accessories ───────────────────────────────────────────────────────────────

class AccessoryType(models.Model):
    """Mouse, Keyboard, Bag, Charger, Headset, USB Hub …"""
    name         = models.CharField(max_length=255, unique=True)
    created_by   = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='created_accessory_types',
    )
    updated_by   = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        related_name='updated_accessory_types', null=True, blank=True,
    )
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True, null=True, blank=True)
    deleted_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'Accessory_Types'

    def __str__(self):
        return self.name


class Accessory(models.Model):
    accessory_type = models.ForeignKey(AccessoryType, on_delete=models.PROTECT, related_name='accessories')
    serial_number  = models.CharField(max_length=255, null=True, blank=True, unique=True)
    brand          = models.ForeignKey(Brand,  on_delete=models.PROTECT, null=True, blank=True, related_name='accessories')
    device         = models.ForeignKey(Device, on_delete=models.SET_NULL, null=True, blank=True, related_name='accessories')
    site           = models.ForeignKey('locations.Site', on_delete=models.PROTECT, related_name='accessories')
    flag           = models.CharField(max_length=20, choices=DeviceFlag.choices, default=DeviceFlag.AVAILABLE)
    notes          = models.TextField(null=True, blank=True)
    created_by     = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='created_accessories',
    )
    updated_by     = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='updated_accessories',
        null=True, blank=True,
    )
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True, null=True, blank=True)
    deleted_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'Accessories'
        permissions = [
            ('link_device_accessory', 'Can link or unlink an accessory to a device'),
        ]

    def __str__(self):
        return f'{self.accessory_type.name} — {self.serial_number or "No S/N"}'

    @property
    def current_assignment(self):
        return self.accessory_assignments.filter(returned_date__isnull=True).first()