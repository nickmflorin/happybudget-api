from django import forms
from django.contrib import admin

from greenbudget.app.common.admin import color_icon

from .models import (
    BudgetAccountGroup,
    TemplateAccountGroup,
    BudgetSubAccountGroup,
    TemplateSubAccountGroup
)


class GroupAdmin(admin.ModelAdmin):
    list_display = (
        "name", "color", "created_at", "created_by", "parent")

    def get_color_for_admin(self, obj):
        if obj.color:
            return color_icon(obj.color.code)
        return u''

    get_color_for_admin.allow_tags = True
    get_color_for_admin.short_description = 'Color'


class BudgetAccountGroupAdminForm(forms.ModelForm):
    class Meta:
        model = BudgetAccountGroup
        fields = '__all__'


class TemplateAccountGroupAdminForm(forms.ModelForm):
    class Meta:
        model = TemplateAccountGroup
        fields = '__all__'


class BudgetAccountGroupAdmin(GroupAdmin):
    form = BudgetAccountGroupAdminForm


class TemplateAccountGroupAdmin(GroupAdmin):
    form = TemplateAccountGroupAdminForm


class BudgetSubAccountGroupAdminForm(forms.ModelForm):
    class Meta:
        model = BudgetSubAccountGroup
        fields = '__all__'


class TemplateSubAccountGroupAdminForm(forms.ModelForm):
    class Meta:
        model = TemplateSubAccountGroup
        fields = '__all__'


class BudgetSubAccountGroupAdmin(GroupAdmin):
    form = BudgetSubAccountGroupAdminForm


class TemplateSubAccountGroupAdmin(GroupAdmin):
    form = TemplateSubAccountGroupAdminForm


admin.site.register(BudgetAccountGroup, BudgetAccountGroupAdmin)
admin.site.register(TemplateAccountGroup, TemplateAccountGroupAdmin)
admin.site.register(BudgetSubAccountGroup, BudgetSubAccountGroupAdmin)
admin.site.register(TemplateSubAccountGroup, TemplateSubAccountGroupAdmin)
