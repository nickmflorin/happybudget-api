from django import forms
from django.contrib import admin

from .models import Actual


class ActualAdminForm(forms.ModelForm):
    class Meta:
        model = Actual
        fields = '__all__'


@admin.register(Actual)
class ActualAdmin(admin.ModelAdmin):
    list_display = (
        "budget", "value", "owner", "created_by", "created_at")
