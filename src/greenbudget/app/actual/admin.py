from django import forms

from greenbudget import harry
from greenbudget.app.tagging.admin import TagAdminForm

from .models import Actual, ActualType


class ActualTypeForm(TagAdminForm):
    class Meta:
        model = ActualType
        fields = ('order', 'title', 'color', 'plaid_transaction_type')


class ActualTypeAdmin(harry.HarryModelAdmin):
    list_display = (
        "title", "get_color_for_admin", "order", "created_at", "updated_at")
    form = ActualTypeForm
    show_in_index = True

    def get_color_for_admin(self, obj):
        if obj.color:
            return harry.utils.color_icon(obj.color.code)
        return u''

    get_color_for_admin.allow_tags = True
    get_color_for_admin.short_description = 'Color'


class ActualAdminForm(forms.ModelForm):
    class Meta:
        model = Actual
        fields = '__all__'


class ActualAdmin(harry.HarryModelAdmin):
    list_display = ("budget", "value", "created_by", "created_at")


harry.site.register(Actual, ActualAdmin)
harry.site.register(ActualType, ActualTypeAdmin)
