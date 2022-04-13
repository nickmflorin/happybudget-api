import nested_admin

from django import forms

from greenbudget import harry
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

    def get_form(self, request, obj=None, **kwargs):
        request.__obj__ = obj
        return super().get_form(request, obj, **kwargs)


harry.site.register(Budget, BudgetAdmin)
