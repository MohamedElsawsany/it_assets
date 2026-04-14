from django import forms
from django.utils.translation import gettext_lazy as _
from .models import (Brand, DeviceCategory, DeviceModel, CPU, GPU,
                     OperatingSystem, Flag, AccessoryType, Device, Accessory)


# ── Lookup helpers ────────────────────────────────────────────────────────────

def _name_form(model_class):
    """Factory: simple ModelForm with only a `name` CharField."""
    class _Form(forms.ModelForm):
        class Meta:
            model   = model_class
            fields  = ['name']
            widgets = {'name': forms.TextInput(attrs={'class': 'form-control'})}
            labels  = {'name': _('Name')}
    _Form.__name__ = f'{model_class.__name__}Form'
    return _Form


BrandForm          = _name_form(Brand)
DeviceCategoryForm = _name_form(DeviceCategory)
OperatingSystemForm= _name_form(OperatingSystem)
FlagForm           = _name_form(Flag)
AccessoryTypeForm  = _name_form(AccessoryType)


class DeviceModelForm(forms.ModelForm):
    class Meta:
        model   = DeviceModel
        fields  = ['name', 'brand', 'category']
        widgets = {
            'name':     forms.TextInput(attrs={'class': 'form-control'}),
            'brand':    forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {'name': _('Name'), 'brand': _('Brand'), 'category': _('Category')}


class CPUForm(forms.ModelForm):
    class Meta:
        model   = CPU
        fields  = ['name', 'brand']
        widgets = {
            'name':  forms.TextInput(attrs={'class': 'form-control'}),
            'brand': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {'name': _('Name'), 'brand': _('Brand')}


class GPUForm(forms.ModelForm):
    class Meta:
        model   = GPU
        fields  = ['name', 'brand']
        widgets = {
            'name':  forms.TextInput(attrs={'class': 'form-control'}),
            'brand': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {'name': _('Name'), 'brand': _('Brand')}


# ── Device / Accessory ────────────────────────────────────────────────────────

class DeviceForm(forms.ModelForm):
    class Meta:
        model  = Device
        fields = [
            'serial_number', 'category', 'brand', 'device_model', 'site', 'flag',
            'cpu', 'gpu', 'ram_size_gb', 'hdd_storage_gb', 'ssd_storage_gb',
            'operating_system', 'screen_size_inch', 'ports_number',
        ]
        widgets = {
            'serial_number':   forms.TextInput(attrs={'class': 'form-control'}),
            'category':        forms.Select(attrs={'class': 'form-select'}),
            'brand':           forms.Select(attrs={'class': 'form-select'}),
            'device_model':    forms.Select(attrs={'class': 'form-select'}),
            'site':            forms.Select(attrs={'class': 'form-select'}),
            'flag':            forms.Select(attrs={'class': 'form-select'}),
            'cpu':             forms.Select(attrs={'class': 'form-select'}),
            'gpu':             forms.Select(attrs={'class': 'form-select'}),
            'operating_system':forms.Select(attrs={'class': 'form-select'}),
            'ram_size_gb':     forms.NumberInput(attrs={'class': 'form-control'}),
            'hdd_storage_gb':  forms.NumberInput(attrs={'class': 'form-control'}),
            'ssd_storage_gb':  forms.NumberInput(attrs={'class': 'form-control'}),
            'screen_size_inch':forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'ports_number':    forms.NumberInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'serial_number':   _('Serial Number'),
            'category':        _('Category'),
            'brand':           _('Brand'),
            'device_model':    _('Model'),
            'site':            _('Site'),
            'flag':            _('Flag'),
            'cpu':             _('CPU'),
            'gpu':             _('GPU'),
            'ram_size_gb':     _('RAM (GB)'),
            'hdd_storage_gb':  _('HDD (GB)'),
            'ssd_storage_gb':  _('SSD (GB)'),
            'operating_system':_('Operating System'),
            'screen_size_inch':_('Screen Size (inches)'),
            'ports_number':    _('Ports'),
        }


class ChangeFlagForm(forms.Form):
    flag = forms.ModelChoiceField(
        queryset=Flag.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label=_('New Flag'),
    )


class AccessoryForm(forms.ModelForm):
    class Meta:
        model  = Accessory
        fields = ['accessory_type', 'serial_number', 'brand', 'device', 'site', 'flag']
        widgets = {
            'accessory_type': forms.Select(attrs={'class': 'form-select'}),
            'serial_number':  forms.TextInput(attrs={'class': 'form-control'}),
            'brand':          forms.Select(attrs={'class': 'form-select'}),
            'device':         forms.Select(attrs={'class': 'form-select'}),
            'site':           forms.Select(attrs={'class': 'form-select'}),
            'flag':           forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'accessory_type': _('Type'),
            'serial_number':  _('Serial Number'),
            'brand':          _('Brand'),
            'device':         _('Linked Device'),
            'site':           _('Site'),
            'flag':           _('Flag'),
        }
