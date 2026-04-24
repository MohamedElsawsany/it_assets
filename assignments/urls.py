from django.urls import path
from . import views

urlpatterns = [
    # Assignments
    path('', views.assignments_index, name='assignments-index'),
    path('data/', views.assignments_data, name='assignments-data'),
    path('create/', views.assignment_create, name='assignment-create'),
    path('<int:pk>/', views.assignment_detail, name='assignment-detail'),
    path('<int:pk>/edit/', views.assignment_edit, name='assignment-edit'),
    path('<int:pk>/return/', views.assignment_return, name='assignment-return'),
    path('<int:pk>/delete/', views.assignment_delete, name='assignment-delete'),

    # Transfers
    path('transfers/', views.transfers_index, name='transfers-index'),
    path('transfers/data/', views.transfers_data, name='transfers-data'),
    path('transfers/create/', views.transfer_create, name='transfer-create'),
    path('transfers/<int:pk>/', views.transfer_detail, name='transfer-detail'),
    path('transfers/<int:pk>/delete/', views.transfer_delete, name='transfer-delete'),
]
