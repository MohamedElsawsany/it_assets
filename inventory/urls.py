from django.urls import path
from . import views

urlpatterns = [
    # Lookups
    path('lookups/', views.lookups_index, name='lookups-index'),
    path('lookups/<str:lookup_type>/data/', views.lookup_data, name='lookup-data'),
    path('lookups/<str:lookup_type>/create/', views.lookup_create, name='lookup-create'),
    path('lookups/<str:lookup_type>/<int:pk>/', views.lookup_item_detail, name='lookup-detail'),
    path('lookups/<str:lookup_type>/<int:pk>/edit/', views.lookup_edit, name='lookup-edit'),
    path('lookups/<str:lookup_type>/<int:pk>/delete/', views.lookup_delete, name='lookup-delete'),

    # Devices
    path('devices/', views.devices_index, name='devices-index'),
    path('devices/data/', views.devices_data, name='devices-data'),
    path('devices/create/', views.device_create, name='device-create'),
    path('devices/<int:pk>/', views.device_detail, name='device-detail'),
    path('devices/<int:pk>/edit/', views.device_edit, name='device-edit'),
    path('devices/<int:pk>/delete/', views.device_delete, name='device-delete'),
    path('devices/<int:pk>/retire/', views.device_retire, name='device-retire'),
    path('devices/<int:pk>/change-flag/', views.device_change_flag, name='device-change-flag'),
    path('devices/<int:pk>/toggle-maintenance/', views.device_toggle_maintenance, name='device-toggle-maintenance'),

    # Accessories
    path('accessories/', views.accessories_index, name='accessories-index'),
    path('accessories/data/', views.accessories_data, name='accessories-data'),
    path('accessories/create/', views.accessory_create, name='accessory-create'),
    path('accessories/<int:pk>/', views.accessory_detail, name='accessory-detail'),
    path('accessories/<int:pk>/edit/', views.accessory_edit, name='accessory-edit'),
    path('accessories/<int:pk>/delete/', views.accessory_delete, name='accessory-delete'),
    path('accessories/<int:pk>/change-flag/', views.accessory_change_flag, name='accessory-change-flag'),
]
