from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from . import views

urlpatterns = [
    path('login/', LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),

    path('users/', views.users_list, name='users-list'),
    path('users/data/', views.users_data, name='users-data'),
    path('users/create/', views.user_create, name='user-create'),
    path('users/<int:user_id>/', views.user_detail, name='user-detail'),
    path('users/<int:user_id>/edit/', views.user_edit, name='user-edit'),
    path('users/<int:user_id>/delete/', views.user_delete, name='user-delete'),
    path('users/<int:user_id>/toggle/', views.user_toggle_status, name='user-toggle'),
    path('users/<int:user_id>/reset-password/', views.user_reset_password, name='user-reset-password'),
    path('users/<int:user_id>/permissions/', views.user_permissions, name='user-permissions'),
    path('users/<int:user_id>/scope/', views.user_scope_save, name='user-scope'),
]
