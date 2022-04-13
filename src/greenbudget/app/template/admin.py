import nested_admin

from django import forms

from greenbudget import harry
from greenbudget.app.account.admin import TemplateAccountInline

from .models import Template


class TemplateAdminForm(forms.ModelForm):
    class Meta:
        model = Template
        fields = ('name', 'image')


@harry.widgets.use_custom_related_field_wrapper
class TemplateAdmin(nested_admin.NestedModelAdmin):
    list_display = ("name", "created_at", "updated_at", "created_by")
    form = TemplateAdminForm
    inlines = [TemplateAccountInline]


harry.site.register(Template, TemplateAdmin)
