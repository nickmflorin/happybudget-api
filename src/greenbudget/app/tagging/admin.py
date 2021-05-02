
from django import forms
from django.contrib import admin

from .models import Color


class ColorAdminForm(forms.ModelForm):
    class Meta:
        model = Color
        fields = '__all__'


class ColorAdmin(admin.ModelAdmin):
    list_display = ("id", "code", "created_at", "get_usage")
    form = ColorAdminForm

    def get_usage(self, obj):
        usages = []
        for content_type in obj.content_types.all():
            usages.append(content_type.model.title())
        return ", ".join(usages)

    get_usage.short_description = 'Usage'


admin.site.register(Color, ColorAdmin)
