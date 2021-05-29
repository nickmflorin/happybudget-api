from django import forms
from django.contrib import admin

from greenbudget.app.common.admin import color_icon
from .models import Fringe, BudgetFringe, TemplateFringe


class FringeForm(forms.ModelForm):
    class Meta:
        model = Fringe
        fields = '__all__'


class FringeAdmin(admin.ModelAdmin):
    list_display = (
        "id", "name", "get_color_for_admin", "rate", "cutoff", "unit", "budget",
        "created_by", "created_at")
    form = FringeForm

    def get_color_for_admin(self, obj):
        if obj.color:
            return color_icon(obj.color.code)
        return u''

    get_color_for_admin.allow_tags = True
    get_color_for_admin.short_description = 'Color'


admin.site.register(BudgetFringe, FringeAdmin)
admin.site.register(TemplateFringe, FringeAdmin)