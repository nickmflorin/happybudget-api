from django import forms

from greenbudget import harry
from greenbudget.app.tagging.admin import TagAdminForm

from .models import (
    SubAccountUnit, BudgetSubAccount, TemplateSubAccount)


class SubAccountUnitForm(TagAdminForm):
    class Meta:
        model = SubAccountUnit
        fields = TagAdminForm.Meta.fields + ('color', )


class SubAccountUnitAdmin(harry.HarryModelAdmin):
    list_display = (
        "title", "get_color_for_admin", "order", "created_at", "updated_at")
    form = SubAccountUnitForm
    show_in_index = True

    def get_color_for_admin(self, obj):
        if obj.color:
            return harry.utils.color_icon(obj.color.code)
        return u''

    get_color_for_admin.allow_tags = True
    get_color_for_admin.short_description = 'Color'


class SubAccountAdmin(harry.HarryModelAdmin):
    list_display = (
        "identifier", "description", "budget", "created_by", "created_at")


class BudgetSubAccountAdminForm(forms.ModelForm):
    class Meta:
        model = BudgetSubAccount
        fields = (
            'identifier', 'description', 'quantity', 'multiplier', 'rate',
            'unit', 'fringes', 'markups', 'group', 'attachments', 'contact'
        )


class TemplateSubAccountAdminForm(forms.ModelForm):
    class Meta:
        model = TemplateSubAccount
        fields = (
            'identifier', 'description', 'quantity', 'multiplier', 'rate',
            'unit', 'fringes', 'markups', 'group'
        )


class BudgetSubAccountAdmin(SubAccountAdmin):
    form = BudgetSubAccountAdminForm


class TemplateSubAccountAdmin(SubAccountAdmin):
    form = TemplateSubAccountAdminForm


harry.site.register(TemplateSubAccount, TemplateSubAccountAdmin)
harry.site.register(BudgetSubAccount, BudgetSubAccountAdmin)
harry.site.register(SubAccountUnit, SubAccountUnitAdmin)
