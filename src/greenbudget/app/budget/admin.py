import nested_admin

from django import forms
from django.contrib import admin

from greenbudget.app.account.admin import BudgetAccountInline

from .models import Budget


class BudgetAdminForm(forms.ModelForm):
    class Meta:
        model = Budget
        fields = ('name', 'image')


class BudgetAdmin(nested_admin.NestedModelAdmin):
    list_display = ("name", "created_at", "updated_at", "created_by")
    form = BudgetAdminForm
    inlines = [BudgetAccountInline]


admin.site.register(Budget, BudgetAdmin)
