from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from .select2_api import select2_data

urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='/dashboard/', permanent=False)),
    path('', include('dashboard.urls')),
    path('accounts/', include('accounts.urls')),
    path('locations/', include('locations.urls')),
    path('employees/', include('employees.urls')),
    path('inventory/', include('inventory.urls')),
    path('assignments/', include('assignments.urls')),
    path('maintenance/', include('maintenance.urls')),
    path('select2/<str:entity>/', select2_data, name='select2-data'),
]
