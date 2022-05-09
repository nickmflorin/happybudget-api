from django import forms

from happybudget import harry

from happybudget.app.budgeting.admin import (
    BudgetingTreePolymorphicOrderedRowModelInline)
from .models import BudgetAccount, TemplateAccount


class AccountAdmin(harry.HarryModelAdmin):
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


@harry.widgets.use_custom_related_field_wrapper
class BudgetAccountInline(BudgetingTreePolymorphicOrderedRowModelInline):
    model = BudgetAccount


class TemplateAccountInline(BudgetingTreePolymorphicOrderedRowModelInline):
    model = TemplateAccount


@harry.widgets.use_custom_related_field_wrapper
class BudgetAccountAdmin(AccountAdmin):
    form = BudgetAccountAdminForm


class TemplateAccountAdmin(AccountAdmin):
    form = TemplateAccountAdminForm


harry.site.register(BudgetAccount, BudgetAccountAdmin)
harry.site.register(TemplateAccount, TemplateAccountAdmin)
