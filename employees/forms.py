from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Department, Employee


class DepartmentForm(forms.ModelForm):
    class Meta:
        model   = Department
        fields  = ['name']
        widgets = {'name': forms.TextInput(attrs={'class': 'form-control'})}
        labels  = {'name': _('Name')}


class EmployeeForm(forms.ModelForm):
    class Meta:
        model   = Employee
        fields  = ['first_name', 'last_name', 'employee_card_id', 'department', 'site']
        widgets = {
            'first_name':       forms.TextInput(attrs={'class': 'form-control'}),
            'last_name':        forms.TextInput(attrs={'class': 'form-control'}),
            'employee_card_id': forms.NumberInput(attrs={'class': 'form-control'}),
            'department':       forms.Select(attrs={'class': 'form-select'}),
            'site':             forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'first_name':       _('First Name'),
            'last_name':        _('Last Name'),
            'employee_card_id': _('Employee Card ID'),
            'department':       _('Department'),
            'site':             _('Site'),
        }
