from django import forms
from django.contrib import admin

from greenbudget.harry.utils import color_icon
from greenbudget.app.tagging.admin import TagAdminForm

from .models import (
    SubAccountUnit, BudgetSubAccount, TemplateSubAccount)


class SubAccountUnitForm(TagAdminForm):
    class Meta:
        model = SubAccountUnit
        fields = TagAdminForm.Meta.fields + ('color', )


@admin.register(SubAccountUnit)
class SubAccountUnitAdmin(admin.ModelAdmin):
    list_display = (
        "title", "get_color_for_admin", "order", "created_at", "updated_at")
    form = SubAccountUnitForm
    show_in_index = True

    def get_color_for_admin(self, obj):
        if obj.color:
            return color_icon(obj.color.code)
        return u''

    get_color_for_admin.allow_tags = True
    get_color_for_admin.short_description = 'Color'


class SubAccountAdmin(admin.ModelAdmin):
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


@admin.register(BudgetSubAccount)
class BudgetSubAccountAdmin(SubAccountAdmin):
    form = BudgetSubAccountAdminForm


@admin.register(TemplateSubAccount)
class TemplateSubAccountAdmin(SubAccountAdmin):
    form = TemplateSubAccountAdminForm
