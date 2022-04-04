import nested_admin

from django import forms
from django.contrib import admin

from greenbudget.harry.widgets import use_custom_related_field_wrapper
from greenbudget.app.account.admin import TemplateAccountInline

from .models import Template


class TemplateAdminForm(forms.ModelForm):
    class Meta:
        model = Template
        fields = ('name', 'image')


@use_custom_related_field_wrapper
class TemplateAdmin(nested_admin.NestedModelAdmin):
    list_display = ("name", "created_at", "updated_at", "created_by")
    form = TemplateAdminForm
    inlines = [TemplateAccountInline]


admin.site.register(Template, TemplateAdmin)
