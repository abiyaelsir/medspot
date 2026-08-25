#name=users/admin.py
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

@admin.action(description="Approve selected pharmacist accounts")
def approve_pharmacists(modeladmin, request, queryset):
    # filter to pharmacists only
    pharmacists = queryset.filter(role="pharmacist", is_verified=False)
    count = pharmacists.update(is_verified=True, is_active=True)
    messages.success(request, f"{count} pharmacist account(s) approved.")

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Role & Verification", {"fields": ("role", "is_verified")}),
    )
    list_display = ("username", "email", "first_name", "last_name", "role", "is_verified", "is_staff")
    list_filter = ("role", "is_verified", "is_staff")
    actions = [approve_pharmacists]