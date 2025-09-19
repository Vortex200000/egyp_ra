# accounts/urls.py

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    # Authentication endpoints
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # User profile endpoints
    path('profile/', views.UserProfileView.as_view(), name='user_profile'),
    path('user-details/', views.user_details, name='user_details'),
    path('change-password/', views.change_password, name='change_password'),
    
    # Utility endpoints
    path('check-email/', views.check_email, name='check_email'),
    path('check-username/', views.check_username, name='check_username'),
]