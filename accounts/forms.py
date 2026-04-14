from django import forms
from django.utils.translation import gettext_lazy as _
from .models import User
from locations.models import Site


class UserCreateForm(forms.ModelForm):
    password = forms.CharField(
        label=_('Password'),
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}),
        min_length=8,
    )
    confirm_password = forms.CharField(
        label=_('Confirm Password'),
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}),
    )
    site = forms.ModelChoiceField(
        queryset=Site.objects.all().order_by('name'),
        required=False,
        empty_label=_('— No site —'),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label=_('Site'),
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'role', 'site', 'is_active']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'first_name': _('First Name'),
            'last_name': _('Last Name'),
            'email': _('Email Address'),
            'role': _('Role'),
            'is_active': _('Active'),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', _("Passwords don't match."))
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class UserEditForm(forms.ModelForm):
    site = forms.ModelChoiceField(
        queryset=Site.objects.all().order_by('name'),
        required=False,
        empty_label=_('— No site —'),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label=_('Site'),
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'role', 'site', 'is_active']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'first_name': _('First Name'),
            'last_name': _('Last Name'),
            'email': _('Email Address'),
            'role': _('Role'),
            'is_active': _('Active'),
        }


class ResetPasswordForm(forms.Form):
    new_password = forms.CharField(
        label=_('New Password'),
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}),
        min_length=8,
    )
    confirm_password = forms.CharField(
        label=_('Confirm New Password'),
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}),
    )

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')
        if new_password and confirm_password and new_password != confirm_password:
            self.add_error('confirm_password', _("Passwords don't match."))
        return cleaned_data
