from django import forms
from django.utils.translation import gettext_lazy as _
from .models import MaintenanceRecord, AccessoryMaintenanceRecord


class MaintenanceForm(forms.ModelForm):
    class Meta:
        model   = MaintenanceRecord
        fields  = ['device', 'issue_description', 'maintenance_type', 'vendor_name', 'sent_date']
        widgets = {
            'device':            forms.Select(attrs={'class': 'form-select'}),
            'issue_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'maintenance_type':  forms.Select(attrs={'class': 'form-select'}),
            'vendor_name':       forms.TextInput(attrs={'class': 'form-control'}),
            'sent_date':         forms.DateTimeInput(
                attrs={'class': 'form-control', 'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M',
            ),
        }
        labels = {
            'device':            _('Device'),
            'issue_description': _('Issue Description'),
            'maintenance_type':  _('Maintenance Type'),
            'vendor_name':       _('Vendor Name'),
            'sent_date':         _('Sent Date'),
        }


class AccessoryMaintenanceForm(forms.ModelForm):
    class Meta:
        model   = AccessoryMaintenanceRecord
        fields  = ['accessory', 'issue_description', 'maintenance_type', 'vendor_name', 'sent_date']
        widgets = {
            'accessory':         forms.Select(attrs={'class': 'form-select'}),
            'issue_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'maintenance_type':  forms.Select(attrs={'class': 'form-select'}),
            'vendor_name':       forms.TextInput(attrs={'class': 'form-control'}),
            'sent_date':         forms.DateTimeInput(
                attrs={'class': 'form-control', 'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M',
            ),
        }
        labels = {
            'accessory':         _('Accessory'),
            'issue_description': _('Issue Description'),
            'maintenance_type':  _('Maintenance Type'),
            'vendor_name':       _('Vendor Name'),
            'sent_date':         _('Sent Date'),
        }


class CloseMaintenanceForm(forms.Form):
    returned_date = forms.DateTimeField(
        widget=forms.DateTimeInput(
            attrs={'class': 'form-control', 'type': 'datetime-local'},
            format='%Y-%m-%dT%H:%M',
        ),
        label=_('Returned Date'),
        input_formats=['%Y-%m-%dT%H:%M'],
    )
    resolution_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        label=_('Resolution Notes'),
    )
    cost = forms.DecimalField(
        required=False,
        min_value=0,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        label=_('Cost'),
    )
