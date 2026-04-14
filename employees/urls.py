from django.urls import path
from . import views

urlpatterns = [
    path('', views.employees_index, name='employees-index'),

    # Departments
    path('departments/data/', views.departments_data, name='departments-data'),
    path('departments/create/', views.department_create, name='department-create'),
    path('departments/<int:pk>/', views.department_detail, name='department-detail'),
    path('departments/<int:pk>/edit/', views.department_edit, name='department-edit'),
    path('departments/<int:pk>/delete/', views.department_delete, name='department-delete'),

    # Employees
    path('data/', views.employees_data, name='employees-data'),
    path('create/', views.employee_create, name='employee-create'),
    path('<int:pk>/', views.employee_detail, name='employee-detail'),
    path('<int:pk>/edit/', views.employee_edit, name='employee-edit'),
    path('<int:pk>/delete/', views.employee_delete, name='employee-delete'),
]
