import nested_admin

from django import forms
from django.contrib import admin

from greenbudget.app.account.models import BudgetAccount

from .models import Budget


class BudgetAdminForm(forms.ModelForm):
    class Meta:
        model = Budget
        fields = ('name', 'image')


class AccountInline(nested_admin.NestedStackedInline):
    model = BudgetAccount
    sortable_field_name = "identifier"
    fields = ('identifier', 'description', 'markups', 'group')


class BudgetAdmin(nested_admin.NestedModelAdmin):
    list_display = ("name", "created_at", "updated_at", "created_by")
    form = BudgetAdminForm
    inlines = [AccountInline]


admin.site.register(Budget, BudgetAdmin)
