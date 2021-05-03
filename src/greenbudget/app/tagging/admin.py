from django import forms
from django.apps import apps
from django.contrib import admin
from django.contrib.contenttypes.models import ContentType

from .models import Color


class ColorAdminForm(forms.ModelForm):
    class Meta:
        model = Color
        fields = '__all__'


def assign_to_factory(model_cls):
    def assign_to(modeladmin, request, queryset):
        ct = ContentType.objects.get_for_model(model_cls)
        for obj in queryset.all():
            obj.content_types.add(ct)
            obj.save()

    assign_to.short_description = 'Assign color to %s' % model_cls.__name__
    return assign_to


class ColorAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "created_at", "get_usage")
    form = ColorAdminForm

    def get_usage(self, obj):
        usages = []
        for content_type in obj.content_types.all():
            usages.append(content_type.model.title())
        return ", ".join(usages)

    get_usage.short_description = 'Usage'

    def get_actions(self, request):
        actions = super().get_actions(request)
        field = Color._meta.get_field('content_types')
        limit_choices_to = field.get_limit_choices_to()
        content_types = ContentType.objects.filter(limit_choices_to)
        for ct in content_types:
            model_cls = apps.get_model(
                model_name=ct.model,
                app_label=ct.app_label
            )
            func = assign_to_factory(model_cls)
            actions['assign_to_%s' % model_cls.__name__.lower()] = (
                func,
                'assign_to_%s' % model_cls.__name__.lower(),
                func.short_description
            )

        return actions


admin.site.register(Color, ColorAdmin)
