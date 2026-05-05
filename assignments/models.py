"""
assignments/models.py
─────────────────────
Models: DeviceAssignment, AccessoryAssignment, DeviceTransfer, DeliveredDeviceHistory

RBAC permissions
────────────────
Auto-created by Django (add / change / delete / view) for every model.

Custom:
  assignments.return_device      – record that a device was returned
  assignments.return_accessory   – record that an accessory was returned
  assignments.approve_transfer   – approve a pending site transfer
  assignments.generate_report    – export / print assignment reports
"""

from django.conf import settings
from django.db import models


class DeviceAssignment(models.Model):
    """Active custody record — NULL returned_date means still assigned."""
    device        = models.ForeignKey('inventory.Device',   on_delete=models.PROTECT, related_name='assignments')
    employee      = models.ForeignKey('employees.Employee', on_delete=models.PROTECT, related_name='assignments')
    assigned_date = models.DateTimeField()
    returned_date = models.DateTimeField(
        null=True, blank=True,
        help_text='NULL = device still with employee',
    )
    notes       = models.TextField(null=True, blank=True)
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='assigned_devices', db_column='Assigned_By',
    )
    returned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='returned_devices', db_column='Returned_By',
        null=True, blank=True,
    )
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        db_table = 'Device_Assignments'
        permissions = [
            ('return_device',   'Can record that a device has been returned by an employee'),
            ('generate_report', 'Can export or print assignment reports'),
        ]

    def __str__(self):
        status = 'Active' if not self.returned_date else 'Returned'
        return f'[{status}] {self.device} → {self.employee}'

    @property
    def is_active(self):
        return self.returned_date is None


class AccessoryAssignment(models.Model):
    """Active custody record for accessories — NULL returned_date means still assigned."""
    accessory     = models.ForeignKey('inventory.Accessory',  on_delete=models.PROTECT, related_name='accessory_assignments')
    employee      = models.ForeignKey('employees.Employee',   on_delete=models.PROTECT, related_name='accessory_assignments')
    assigned_date = models.DateTimeField()
    returned_date = models.DateTimeField(
        null=True, blank=True,
        help_text='NULL = accessory still with employee',
    )
    notes       = models.TextField(null=True, blank=True)
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='assigned_accessories', db_column='Assigned_By',
    )
    returned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='returned_accessories', db_column='Returned_By',
        null=True, blank=True,
    )
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        db_table = 'Accessory_Assignments'
        permissions = [
            ('return_accessory', 'Can record that an accessory has been returned by an employee'),
        ]

    def __str__(self):
        status = 'Active' if not self.returned_date else 'Returned'
        return f'[{status}] {self.accessory} → {self.employee}'

    @property
    def is_active(self):
        return self.returned_date is None


class DeviceTransfer(models.Model):
    """Records a device moving from one site to another."""
    device        = models.ForeignKey('inventory.Device', on_delete=models.PROTECT, related_name='transfers')
    from_site     = models.ForeignKey('locations.Site',   on_delete=models.PROTECT, related_name='outgoing_transfers')
    to_site       = models.ForeignKey('locations.Site',   on_delete=models.PROTECT, related_name='incoming_transfers')
    transfer_date = models.DateTimeField()
    notes         = models.TextField(null=True, blank=True)
    transferred_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='device_transfers', db_column='Transferred_By',
    )
    created_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'Device_Transfers'
        permissions = [
            ('approve_transfer', 'Can approve a pending device site transfer'),
        ]

    def __str__(self):
        return f'{self.device} | {self.from_site} → {self.to_site}'


class DeliveredDeviceHistory(models.Model):
    """
    Immutable snapshot written at delivery time.
    Names are stored as strings so history survives lookup changes.
    """
    serial_number       = models.CharField(max_length=255)
    category_name       = models.CharField(max_length=255)
    brand_name          = models.CharField(max_length=255)
    device_model_name   = models.CharField(max_length=255)
    cpu_name            = models.CharField(max_length=255, null=True, blank=True)
    gpu_name            = models.CharField(max_length=255, null=True, blank=True)
    hdd_storage_gb      = models.PositiveIntegerField(null=True, blank=True)
    ssd_storage_gb      = models.PositiveIntegerField(null=True, blank=True)
    ram_size_gb         = models.PositiveSmallIntegerField(null=True, blank=True)
    screen_size_inch    = models.FloatField(null=True, blank=True)
    operating_system_name = models.CharField(max_length=255, null=True, blank=True)
    governorate_name    = models.CharField(max_length=255)
    site_name           = models.CharField(max_length=255)
    ports_number        = models.PositiveSmallIntegerField(null=True, blank=True)

    # Live FK links for traceability (nullable — history survives deletions)
    device   = models.ForeignKey('inventory.Device',   on_delete=models.SET_NULL, null=True, blank=True, related_name='delivery_history')
    employee = models.ForeignKey('employees.Employee', on_delete=models.SET_NULL, null=True, blank=True, related_name='delivery_history')

    created_by   = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='created_delivery_history', db_column='Created_By',
    )
    created_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'Delivered_Devices_History'

    def __str__(self):
        return f'{self.serial_number} → {self.site_name} ({self.created_date.date()})'