"""
employees/models.py
───────────────────
RBAC permissions
────────────────
Auto-created by Django:
  employees.add_department      employees.add_employee
  employees.change_department   employees.change_employee
  employees.delete_department   employees.delete_employee
  employees.view_department     employees.view_employee

Custom:
  employees.print_acknowledgment – print employee asset acknowledgment forms
"""

from django.conf import settings
from django.db import models


class Department(models.Model):
    name         = models.CharField(max_length=255, unique=True)
    created_by   = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='created_departments', db_column='Created_By',
    )
    updated_by   = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        related_name='updated_departments', null=True, blank=True,
    )
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True, null=True, blank=True)
    deleted_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'Departments'

    def __str__(self):
        return self.name


class Employee(models.Model):
    full_name        = models.CharField(max_length=255)
    employee_card_id = models.BigIntegerField(unique=True)
    department       = models.ForeignKey(
        Department, on_delete=models.PROTECT, related_name='employees',
    )
    site = models.ForeignKey(
        'locations.Site', on_delete=models.PROTECT, related_name='employees',
    )
    created_by   = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='created_employees', db_column='Created_By',
    )
    updated_by   = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        related_name='updated_employees', null=True, blank=True,
    )
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True, null=True, blank=True)
    deleted_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'Employees'
        permissions = [
            ('print_acknowledgment', 'Can print employee asset acknowledgment forms'),
            ('export_employee', 'Can export employee data to a file'),
        ]

    def __str__(self):
        return self.full_name