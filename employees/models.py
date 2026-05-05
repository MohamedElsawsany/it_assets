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
  employees.transfer_employee   – move an employee to a different site/dept
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
    first_name       = models.CharField(max_length=255)
    last_name        = models.CharField(max_length=255)
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
            ('transfer_employee', 'Can transfer an employee to a different site or department'),
        ]

    def __str__(self):
        return f'{self.first_name} {self.last_name}'

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'