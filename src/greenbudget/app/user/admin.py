from django import forms
from django.contrib import admin

from .models import User


class UserAdminForm(forms.ModelForm):
    class Meta:
        model = User
        fields = '__all__'


class UserAdmin(admin.ModelAdmin):
    list_display = (
        "first_name", "last_name", "email", "created_at", "last_login")
    form = UserAdminForm


admin.site.register(User, UserAdmin)
