import logging
from polymorphic.admin import (
    PolymorphicParentModelAdmin, PolymorphicChildModelFilter,
    PolymorphicChildModelAdmin)

from django import forms
from django.apps import apps
from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError, models

from greenbudget.harry.widgets import use_custom_related_field_wrapper
from greenbudget.harry.utils import color_icon

from greenbudget.app.subaccount.models import SubAccountUnit

from .models import Color, Tag


logger = logging.getLogger("greenbudget")


class ColorAdminForm(forms.ModelForm):
    class Meta:
        model = Color
        fields = '__all__'


class TagAdminForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ('order', 'title', 'plural_title')

    def clean(self):
        data = super().clean()
        # I don't understand why, but Django seems to handle the validation of
        # the constraint:
        #   unique_together = (('title', 'polymorphic_ctype_id'))
        # properly when updating a model, but not when creating the model.
        if self.instance.pk is None:
            q = models.Q(title=data['title'])
            existing = self.Meta.model.objects.filter(q)
            if existing.count() != 0:
                raise forms.ValidationError(
                    "A model with this title already exists.")
        return data


def assign_to_factory(model_cls):
    def assign_to(modeladmin, request, queryset):
        ct = ContentType.objects.get_for_model(model_cls)
        for obj in queryset.all():
            obj.content_types.add(ct)
            try:
                obj.save()
            # If there is a field that is required on the instance but not
            # provided - the form for that instance is not in a state in which
            # the instance can be saved without updating the field in the form.
            # For this edge case, just ignore the action on that instance.
            except IntegrityError as e:
                logger.error("Cannot perform action on color: %s." % str(e))

    assign_to.short_description = 'Assign color to %s' % model_cls.__name__
    return assign_to


@admin.register(Tag)
@use_custom_related_field_wrapper
class TagAdmin(PolymorphicParentModelAdmin):
    base_model = Tag
    child_models = (SubAccountUnit,)
    list_filter = (PolymorphicChildModelFilter,)
    list_display = ("get_tag_type", "title", "order", "created_at", "updated_at")
    form = TagAdminForm
    show_in_index = True

    def get_tag_type(self, obj):
        ct = ContentType.objects.get(pk=obj.polymorphic_ctype_id)
        model_cls = ct.model_class()
        return getattr(model_cls._meta, 'verbose_name', model_cls.__name__)

    get_tag_type.short_description = 'Type'


class TagChildAdmin(PolymorphicChildModelAdmin):
    base_model = Tag


@admin.register(Color)
@use_custom_related_field_wrapper
class ColorAdmin(admin.ModelAdmin):
    list_display = (
        "get_color_for_admin", "name", "code", "created_at", "get_usage")
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

    def get_color_for_admin(self, obj):
        return color_icon(obj.code)

    get_color_for_admin.allow_tags = True
    get_color_for_admin.short_description = 'Color'
