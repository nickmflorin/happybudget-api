from django import forms
from django.contrib import admin
from django.utils.html import mark_safe

from .models import User


class UserAdminForm(forms.ModelForm):
    class Meta:
        model = User
        fields = '__all__'


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        "first_name", "last_name", "email", "created_at", "last_login",
        "is_admin", "is_staff", "is_superuser", "email_actions")
    fieldsets = (
        ('Profile info', {
            'fields': (
                'first_name', 'last_name', 'position', 'company',
                'address', 'phone_number', 'timezone', 'profile_image')
        }),
        ('Restrictions & Permissions', {
            'fields': (
                'is_admin', 'is_superuser', 'is_staff', 'is_verified',
                'is_first_time'
            )
        }),
    )
    form = UserAdminForm

    def email_actions(self, instance):
        return mark_safe(u"""
            <div style="display: flex; flex-direction: row;">
                <a class="link">Send Email Verification</a>
                <span class="link" style="margin-left: 5px; margin-right: 5px;">
                  |
                </span>
                <a class="link">Send Forgot Password</a>
            </div>
        """)

    email_actions.allow_tags = True
