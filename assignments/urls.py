from django.urls import path
from . import views

urlpatterns = [
    # Device Assignments
    path('', views.assignments_index, name='assignments-index'),
    path('data/', views.assignments_data, name='assignments-data'),
    path('create/', views.assignment_create, name='assignment-create'),
    path('<int:pk>/', views.assignment_detail, name='assignment-detail'),
    path('<int:pk>/return/', views.assignment_return, name='assignment-return'),

    # Accessory Assignments
    path('accessories/data/', views.acc_assignments_data, name='acc-assignments-data'),
    path('accessories/create/', views.acc_assignment_create, name='acc-assignment-create'),
    path('accessories/<int:pk>/', views.acc_assignment_detail, name='acc-assignment-detail'),
    path('accessories/<int:pk>/return/', views.acc_assignment_return, name='acc-assignment-return'),

    # Transfers — index
    path('transfers/', views.transfers_index, name='transfers-index'),

    # Device Transfers
    path('transfers/devices/data/', views.device_transfers_data, name='device-transfers-data'),
    path('transfers/devices/create/', views.device_transfer_create, name='device-transfer-create'),
    path('transfers/devices/available/', views.transfer_available_devices, name='transfer-available-devices'),
    path('transfers/devices/<int:pk>/', views.transfer_detail, name='transfer-detail'),
    path('transfers/devices/<int:pk>/accept/', views.device_transfer_accept, name='device-transfer-accept'),
    path('transfers/devices/<int:pk>/reject/', views.device_transfer_reject, name='device-transfer-reject'),
    path('transfers/devices/<int:pk>/delete/', views.device_transfer_delete, name='device-transfer-delete'),

    # Accessory Transfers
    path('transfers/accessories/data/', views.accessory_transfers_data, name='accessory-transfers-data'),
    path('transfers/accessories/create/', views.accessory_transfer_create, name='accessory-transfer-create'),
    path('transfers/accessories/available/', views.transfer_available_accessories, name='transfer-available-accessories'),
    path('transfers/accessories/<int:pk>/', views.accessory_transfer_detail, name='accessory-transfer-detail'),
    path('transfers/accessories/<int:pk>/accept/', views.accessory_transfer_accept, name='accessory-transfer-accept'),
    path('transfers/accessories/<int:pk>/reject/', views.accessory_transfer_reject, name='accessory-transfer-reject'),
    path('transfers/accessories/<int:pk>/delete/', views.accessory_transfer_delete, name='accessory-transfer-delete'),

    # Export endpoints
    path('export/', views.assignments_export, name='assignments-export'),
    path('accessories/export/', views.acc_assignments_export, name='acc-assignments-export'),
    path('transfers/devices/export/', views.device_transfers_export, name='device-transfers-export'),
    path('transfers/accessories/export/', views.accessory_transfers_export, name='accessory-transfers-export'),
]
