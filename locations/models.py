"""
locations/models.py
───────────────────
RBAC permissions
────────────────
Auto-created by Django for each model (add / change / delete / view).
No extra custom permissions needed here — CRUD is sufficient.

  locations.add_governorate     locations.add_site
  locations.change_governorate  locations.change_site
  locations.delete_governorate  locations.delete_site
  locations.view_governorate    locations.view_site
"""

from django.conf import settings
from django.db import models


class Governorate(models.Model):
    name         = models.CharField(max_length=255, unique=True)
    created_by   = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='created_governorates', db_column='Created_By',
    )
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True, null=True, blank=True)
    deleted_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'Governorates'

    def __str__(self):
        return self.name


class Site(models.Model):
    name         = models.CharField(max_length=255, unique=True)
    governorate  = models.ForeignKey(
        Governorate, on_delete=models.PROTECT, related_name='sites',
    )
    created_by   = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='created_sites', db_column='Created_By',
    )
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True, null=True, blank=True)
    deleted_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'Sites'

    def __str__(self):
        return self.name