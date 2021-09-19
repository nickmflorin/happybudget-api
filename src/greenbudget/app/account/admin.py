from django import forms
from django.contrib import admin

from .models import BudgetAccount, TemplateAccount


class AccountAdmin(admin.ModelAdmin):
    list_display = (
        "identifier", "description", "parent", "created_by", "created_at")


class BudgetAccountAdminForm(forms.ModelForm):
    class Meta:
        model = BudgetAccount
        fields = '__all__'


class TemplateAccountAdminForm(forms.ModelForm):
    class Meta:
        model = TemplateAccount
        fields = '__all__'


class BudgetAccountAdmin(AccountAdmin):
    form = BudgetAccountAdminForm


class TemplateAccountAdmin(AccountAdmin):
    form = TemplateAccountAdminForm


admin.site.register(BudgetAccount, BudgetAccountAdmin)
admin.site.register(TemplateAccount, TemplateAccountAdmin)
