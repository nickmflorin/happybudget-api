from django import forms
from django.contrib import admin
from django.contrib.contenttypes.models import ContentType

from greenbudget.app.common.admin import color_icon
from .models import SubAccountUnit


class SubAccountUnitForm(forms.ModelForm):
    class Meta:
        model = SubAccountUnit
        fields = '__all__'


def assign_to_factory(model_cls):
    def assign_to(modeladmin, request, queryset):
        ct = ContentType.objects.get_for_model(model_cls)
        for obj in queryset.all():
            obj.content_types.add(ct)
            obj.save()

    assign_to.short_description = 'Assign color to %s' % model_cls.__name__
    return assign_to


class SubAccountUnitAdmin(admin.ModelAdmin):
    list_display = (
        "title", "get_color_for_admin", "order", "created_at", "updated_at")
    form = SubAccountUnitForm

    def get_color_for_admin(self, obj):
        if obj.color:
            return color_icon(obj.color.code)
        return u''

    get_color_for_admin.allow_tags = True
    get_color_for_admin.short_description = 'Color'


admin.site.register(SubAccountUnit, SubAccountUnitAdmin)
