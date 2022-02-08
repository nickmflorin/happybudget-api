from django import forms
from django.contrib import admin

from greenbudget.harry.utils import color_icon
from greenbudget.app.tagging.admin import TagAdminForm

from .models import Actual, ActualType


class ActualTypeForm(TagAdminForm):
    class Meta:
        model = ActualType
        fields = ('order', 'title', 'color')


@admin.register(ActualType)
class ActualTypeAdmin(admin.ModelAdmin):
    list_display = (
        "title", "get_color_for_admin", "order", "created_at", "updated_at")
    form = ActualTypeForm
    show_in_index = True

    def get_color_for_admin(self, obj):
        if obj.color:
            return color_icon(obj.color.code)
        return u''

    get_color_for_admin.allow_tags = True
    get_color_for_admin.short_description = 'Color'


class ActualAdminForm(forms.ModelForm):
    class Meta:
        model = Actual
        fields = '__all__'


@admin.register(Actual)
class ActualAdmin(admin.ModelAdmin):
    list_display = ("budget", "value", "created_by", "created_at")
