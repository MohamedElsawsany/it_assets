"""
accounts/models.py
──────────────────
Access control uses Django's per-user permission system (user.has_perm / user.user_permissions).
Site scope controls which branches' data the user can see.
"""

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('Email is required'))
        email = self.normalize_email(email)
        user  = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff',     True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):

    # ── Site scope ────────────────────────────────────────────────────────────
    class SiteScope(models.TextChoices):
        ALL      = 'all',      _('All Branches')
        OWN      = 'own',      _('Own Branch Only')
        SPECIFIC = 'specific', _('Specific Branches')

    # ── Fields ────────────────────────────────────────────────────────────────
    first_name = models.CharField(max_length=255)
    last_name  = models.CharField(max_length=255)
    email      = models.EmailField(max_length=255, unique=True)

    # Primary site FK — kept for backward compatibility and as default own_site.
    site = models.ForeignKey(
        'locations.Site',
        on_delete=models.PROTECT,
        related_name='users',
        null=True, blank=True,
    )

    # Site scope: controls which branches' data this user can access.
    site_scope = models.CharField(
        max_length=10,
        choices=SiteScope.choices,
        default=SiteScope.OWN,
        verbose_name=_('Site Scope'),
    )
    own_site = models.ForeignKey(
        'locations.Site',
        on_delete=models.SET_NULL,
        related_name='own_users',
        null=True, blank=True,
        verbose_name=_('Own Site'),
        help_text=_('Used when site scope is "Own Branch Only".'),
    )
    allowed_sites = models.ManyToManyField(
        'locations.Site',
        related_name='allowed_users',
        blank=True,
        verbose_name=_('Allowed Sites'),
        help_text=_('Used when site scope is "Specific Branches".'),
    )

    is_active = models.BooleanField(default=True)
    is_staff  = models.BooleanField(default=False)

    created_by   = models.ForeignKey(
        'self', on_delete=models.PROTECT,
        related_name='created_users',
        null=True, blank=True,
        db_column='Created_By',
    )
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True, null=True, blank=True)
    deleted_date = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        db_table = 'Users'
        permissions = [
            ('reset_password_user', 'Can reset another user\'s password'),
            ('activate_user',       'Can activate or deactivate users'),
        ]

    def __str__(self):
        return f'{self.first_name} {self.last_name}'

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    def get_allowed_sites(self):
        """
        Returns a Site queryset representing every branch this user may access.

        Rules:
          is_superuser or site_scope='all'      -> all sites
          site_scope='specific'                  -> allowed_sites M2M
          site_scope='own' (default)             -> own_site FK, falling back to site FK
          no site at all (own scope)             -> empty queryset
        """
        from locations.models import Site
        if self.is_superuser or self.site_scope == self.SiteScope.ALL:
            return Site.objects.all()
        if self.site_scope == self.SiteScope.SPECIFIC:
            return self.allowed_sites.all()
        # OWN — prefer own_site, fall back to legacy site FK
        anchor = self.own_site_id or self.site_id
        if anchor:
            return Site.objects.filter(pk=anchor)
        return Site.objects.none()
