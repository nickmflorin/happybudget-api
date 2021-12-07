from django import forms
from django.contrib import admin

from .models import User, UnapprovedUser


class UserAdminForm(forms.ModelForm):
    class Meta:
        model = User
        fields = (
            'first_name', 'last_name', 'email', 'is_admin', 'is_superuser',
            'is_staff', 'timezone', 'profile_image', 'is_verified',
            'is_first_time')


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        "first_name", "last_name", "email", "created_at", "last_login",
        "is_admin", "is_staff", "is_superuser")
    form = UserAdminForm


@admin.action(description='Mark selected users as approved.')
def make_approved(modeladmin, request, queryset):
    queryset.update(is_approved=True)


class UnapprovedUserAdminForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('is_approved', )


@admin.register(UnapprovedUser)
class UnapprovedUserAdmin(admin.ModelAdmin):
    actions = [make_approved]
    form = UnapprovedUserAdminForm
    list_display = (
        "first_name", "last_name", "email", "created_at", "is_verified")
