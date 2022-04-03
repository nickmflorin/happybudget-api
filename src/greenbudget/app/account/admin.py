from django import forms
from django.contrib import admin

from greenbudget.app.budgeting.admin import (
    BudgetingTreePolymorphicOrderedRowModelInline)
from .models import BudgetAccount, TemplateAccount


class AccountAdmin(admin.ModelAdmin):
    list_display = (
        "identifier", "description", "parent", "created_by", "created_at")


class BudgetAccountAdminForm(forms.ModelForm):
    class Meta:
        model = BudgetAccount
        fields = ('identifier', 'description', 'markups', 'group')


class TemplateAccountAdminForm(forms.ModelForm):
    class Meta:
        model = TemplateAccount
        fields = ('identifier', 'description', 'markups', 'group')


class BudgetAccountInline(BudgetingTreePolymorphicOrderedRowModelInline):
    model = BudgetAccount


class TemplateAccountInline(BudgetingTreePolymorphicOrderedRowModelInline):
    model = TemplateAccount


class BudgetAccountAdmin(AccountAdmin):
    form = BudgetAccountAdminForm


class TemplateAccountAdmin(AccountAdmin):
    form = TemplateAccountAdminForm


admin.site.register(BudgetAccount, BudgetAccountAdmin)
admin.site.register(TemplateAccount, TemplateAccountAdmin)
