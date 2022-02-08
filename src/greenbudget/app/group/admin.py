from django import forms
from django.contrib import admin

from greenbudget.harry.utils import color_icon

from .models import Group


class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = '__all__'


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    form = GroupForm
    list_display = (
        "name", "get_color_for_admin", "created_at", "created_by", "parent")

    def get_color_for_admin(self, obj):
        if obj.color:
            return color_icon(obj.color.code)
        return u''

    get_color_for_admin.allow_tags = True
    get_color_for_admin.short_description = 'Color'
