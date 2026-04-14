from django.urls import path
from . import views

urlpatterns = [
    path('', views.locations_index, name='locations-index'),

    # Governorates
    path('governorates/data/', views.governorates_data, name='governorates-data'),
    path('governorates/create/', views.governorate_create, name='governorate-create'),
    path('governorates/<int:pk>/', views.governorate_detail, name='governorate-detail'),
    path('governorates/<int:pk>/edit/', views.governorate_edit, name='governorate-edit'),
    path('governorates/<int:pk>/delete/', views.governorate_delete, name='governorate-delete'),

    # Sites
    path('sites/data/', views.sites_data, name='sites-data'),
    path('sites/create/', views.site_create, name='site-create'),
    path('sites/<int:pk>/', views.site_detail, name='site-detail'),
    path('sites/<int:pk>/edit/', views.site_edit, name='site-edit'),
    path('sites/<int:pk>/delete/', views.site_delete, name='site-delete'),
]
