from django import forms

from greenbudget import harry

from .models import Fringe, BudgetFringe, TemplateFringe


class FringeForm(forms.ModelForm):
    class Meta:
        model = Fringe
        fields = '__all__'


class FringeAdmin(harry.HarryModelAdmin):
    list_display = (
        "id", "name", "get_color_for_admin", "rate", "cutoff", "unit", "budget",
        "created_by", "created_at")
    form = FringeForm

    def get_color_for_admin(self, obj):
        if obj.color:
            return harry.utils.color_icon(obj.color.code)
        return u''

    get_color_for_admin.allow_tags = True
    get_color_for_admin.short_description = 'Color'


harry.site.register(BudgetFringe, FringeAdmin)
harry.site.register(TemplateFringe, FringeAdmin)
