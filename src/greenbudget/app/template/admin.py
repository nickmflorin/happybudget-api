import nested_admin

from django import forms
from django.contrib import admin

from greenbudget.app.account.models import TemplateAccount

from .models import Template


class TemplateAdminForm(forms.ModelForm):
    class Meta:
        model = Template
        fields = ('name', 'image')


class AccountInline(nested_admin.NestedStackedInline):
    model = TemplateAccount
    sortable_field_name = "identifier"
    fields = ('identifier', 'description', 'markups', 'group')


class TemplateAdmin(nested_admin.NestedModelAdmin):
    list_display = ("name", "created_at", "updated_at", "created_by")
    form = TemplateAdminForm
    inlines = [AccountInline]


admin.site.register(Template, TemplateAdmin)
