# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserProfile

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'username', 'first_name', 'last_name', 'is_staff', 'is_verified', 'created_at')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'is_verified')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('-created_at',)
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('phone', 'date_of_birth', 'profile_picture', 'is_verified')
        }),
    )

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'location', 'emergency_contact_name')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
