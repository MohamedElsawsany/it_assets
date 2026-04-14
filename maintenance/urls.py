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
]
