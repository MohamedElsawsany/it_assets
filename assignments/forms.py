from django import forms
from django.utils.translation import gettext_lazy as _
from .models import DeviceAssignment, AccessoryAssignment, DeviceTransfer


class AssignmentForm(forms.ModelForm):
    class Meta:
        model   = DeviceAssignment
        fields  = ['device', 'employee', 'assigned_date', 'notes']
        widgets = {
            'device':        forms.Select(attrs={'class': 'form-select'}),
            'employee':      forms.Select(attrs={'class': 'form-select'}),
            'assigned_date': forms.DateTimeInput(
                attrs={'class': 'form-control', 'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M',
            ),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'device':        _('Device'),
            'employee':      _('Employee'),
            'assigned_date': _('Assignment Date'),
            'notes':         _('Notes'),
        }


class ReturnDeviceForm(forms.Form):
    returned_date = forms.DateTimeField(
        widget=forms.DateTimeInput(
            attrs={'class': 'form-control', 'type': 'datetime-local'},
            format='%Y-%m-%dT%H:%M',
        ),
        label=_('Return Date'),
        input_formats=['%Y-%m-%dT%H:%M'],
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        label=_('Return Notes'),
    )


class AccessoryAssignmentForm(forms.ModelForm):
    class Meta:
        model   = AccessoryAssignment
        fields  = ['accessory', 'employee', 'assigned_date', 'notes']
        widgets = {
            'accessory':     forms.Select(attrs={'class': 'form-select'}),
            'employee':      forms.Select(attrs={'class': 'form-select'}),
            'assigned_date': forms.DateTimeInput(
                attrs={'class': 'form-control', 'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M',
            ),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'accessory':     _('Accessory'),
            'employee':      _('Employee'),
            'assigned_date': _('Assignment Date'),
            'notes':         _('Notes'),
        }


class TransferForm(forms.ModelForm):
    class Meta:
        model   = DeviceTransfer
        fields  = ['device', 'from_site', 'to_site', 'transfer_date', 'notes']
        widgets = {
            'device':        forms.Select(attrs={'class': 'form-select'}),
            'from_site':     forms.Select(attrs={'class': 'form-select'}),
            'to_site':       forms.Select(attrs={'class': 'form-select'}),
            'transfer_date': forms.DateTimeInput(
                attrs={'class': 'form-control', 'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M',
            ),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'device':        _('Device'),
            'from_site':     _('From Site'),
            'to_site':       _('To Site'),
            'transfer_date': _('Transfer Date'),
            'notes':         _('Notes'),
        }
