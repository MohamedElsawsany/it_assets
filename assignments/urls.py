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

    # Transfers
    path('transfers/', views.transfers_index, name='transfers-index'),
    path('transfers/data/', views.transfers_data, name='transfers-data'),
    path('transfers/create/', views.transfer_create, name='transfer-create'),
    path('transfers/<int:pk>/', views.transfer_detail, name='transfer-detail'),
    path('transfers/<int:pk>/delete/', views.transfer_delete, name='transfer-delete'),
]
