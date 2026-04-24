"""
maintenance/models.py
─────────────────────
RBAC permissions
────────────────
Auto-created by Django:
  maintenance.add_maintenancerecord
  maintenance.change_maintenancerecord
  maintenance.delete_maintenancerecord
  maintenance.view_maintenancerecord

Custom:
  maintenance.close_maintenancerecord  – set returned_date and resolution notes
  maintenance.view_cost                – see the cost field (sensitive financial data)
"""

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class MaintenanceRecord(models.Model):

    class MaintenanceType(models.TextChoices):
        INTERNAL = 'Internal', _('Internal')
        EXTERNAL = 'External', _('External (Vendor)')

    device            = models.ForeignKey('inventory.Device', on_delete=models.PROTECT, related_name='maintenance_records')
    previous_flag     = models.CharField(max_length=50, blank=True, default='', help_text='Device flag before entering maintenance; restored on close')
    issue_description = models.TextField()
    maintenance_type  = models.CharField(
        max_length=20,
        choices=MaintenanceType.choices,
        default=MaintenanceType.INTERNAL,
    )
    vendor_name     = models.CharField(max_length=255, null=True, blank=True, help_text='Fill if external maintenance')
    sent_date       = models.DateTimeField()
    returned_date   = models.DateTimeField(null=True, blank=True, help_text='NULL = still under maintenance')
    resolution_notes = models.TextField(null=True, blank=True)
    cost            = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(0)],
    )
    created_by   = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='created_maintenance_records', db_column='Created_By',
    )
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        db_table = 'Maintenance_Records'
        permissions = [
            ('close_maintenancerecord', 'Can close a maintenance record and add resolution notes'),
            ('view_cost',               'Can view the financial cost field on a maintenance record'),
        ]

    def __str__(self):
        status = 'Open' if not self.returned_date else 'Closed'
        return f'[{status}] {self.device} — {self.sent_date.date()}'

    @property
    def is_open(self):
        return self.returned_date is None