from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Governorate, Site


class GovernorateForm(forms.ModelForm):
    class Meta:
        model   = Governorate
        fields  = ['name']
        widgets = {'name': forms.TextInput(attrs={'class': 'form-control'})}
        labels  = {'name': _('Name')}


class SiteForm(forms.ModelForm):
    class Meta:
        model   = Site
        fields  = ['name', 'governorate']
        widgets = {
            'name':        forms.TextInput(attrs={'class': 'form-control'}),
            'governorate': forms.Select(attrs={'class': 'form-select'}),
        }
        labels  = {'name': _('Name'), 'governorate': _('Governorate')}
