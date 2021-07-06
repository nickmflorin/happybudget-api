from django import forms
from django.contrib import admin

from .models import Budget


class BudgetAdminForm(forms.ModelForm):
    class Meta:
        model = Budget
        fields = '__all__'


class BudgetAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at", "updated_at", "created_by")
    form = BudgetAdminForm


admin.site.register(Budget, BudgetAdmin)
