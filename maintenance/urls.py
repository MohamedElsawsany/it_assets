from django.urls import path
from . import views

urlpatterns = [
    path('', views.maintenance_index, name='maintenance-index'),
    path('data/', views.maintenance_data, name='maintenance-data'),
    path('create/', views.maintenance_create, name='maintenance-create'),
    path('<int:pk>/', views.maintenance_detail, name='maintenance-detail'),
    path('<int:pk>/edit/', views.maintenance_edit, name='maintenance-edit'),
    path('<int:pk>/close/', views.maintenance_close, name='maintenance-close'),
    path('<int:pk>/delete/', views.maintenance_delete, name='maintenance-delete'),

    # Accessory Maintenance
    path('accessories/data/', views.acc_maintenance_data, name='acc-maintenance-data'),
    path('accessories/create/', views.acc_maintenance_create, name='acc-maintenance-create'),
    path('accessories/<int:pk>/', views.acc_maintenance_detail, name='acc-maintenance-detail'),
    path('accessories/<int:pk>/edit/', views.acc_maintenance_edit, name='acc-maintenance-edit'),
    path('accessories/<int:pk>/close/', views.acc_maintenance_close, name='acc-maintenance-close'),
    path('accessories/<int:pk>/delete/', views.acc_maintenance_delete, name='acc-maintenance-delete'),
]
