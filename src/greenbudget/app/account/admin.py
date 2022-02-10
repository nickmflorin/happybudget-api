import nested_admin

from django import forms
from django.contrib import admin

from .models import BudgetAccount, TemplateAccount


class AccountAdmin(admin.ModelAdmin):
    list_display = (
        "identifier", "description", "parent", "created_by", "created_at")


class AccountInline(nested_admin.NestedStackedInline):
    sortable_field_name = "identifier"
    fields = ('identifier', 'description', 'markups', 'group')


class BudgetAccountAdminForm(forms.ModelForm):
    class Meta:
        model = BudgetAccount
        fields = ('identifier', 'description', 'markups', 'group')


class TemplateAccountAdminForm(forms.ModelForm):
    class Meta:
        model = TemplateAccount
        fields = ('identifier', 'description', 'markups', 'group')


class BudgetAccountInline(AccountInline):
    model = BudgetAccount


class TemplateAccountInline(AccountInline):
    model = TemplateAccount


class BudgetAccountAdmin(AccountAdmin):
    form = BudgetAccountAdminForm


class TemplateAccountAdmin(AccountAdmin):
    form = TemplateAccountAdminForm


admin.site.register(BudgetAccount, BudgetAccountAdmin)
admin.site.register(TemplateAccount, TemplateAccountAdmin)
