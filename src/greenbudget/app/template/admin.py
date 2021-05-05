from django import forms
from django.contrib import admin

from .models import Template


class TemplateAdminForm(forms.ModelForm):
    class Meta:
        model = Template
        fields = '__all__'


class TemplateAdmin(admin.ModelAdmin):
    list_display = (
        "name", "created_at", "updated_at", "created_by", "trash", "community")
    form = TemplateAdminForm


admin.site.register(Template, TemplateAdmin)
