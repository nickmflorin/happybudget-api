from django import forms
from django.contrib import admin

from .models import User


class UserAdminForm(forms.ModelForm):
    class Meta:
        model = User
        fields = (
            'first_name', 'last_name', 'email', 'is_admin', 'is_superuser',
            'is_staff', 'timezone', 'profile_image', 'is_verified',
            'is_first_time')


class UserAdmin(admin.ModelAdmin):
    list_display = (
        "first_name", "last_name", "email", "created_at", "last_login",
        "is_admin", "is_staff", "is_superuser")
    form = UserAdminForm


admin.site.register(User, UserAdmin)
