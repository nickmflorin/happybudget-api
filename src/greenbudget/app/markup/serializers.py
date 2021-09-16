from rest_framework import serializers, exceptions

from greenbudget.lib.drf.serializers import ModelSerializer
from greenbudget.lib.drf.fields import ModelChoiceField

from greenbudget.app.account.models import BudgetAccount
from greenbudget.app.budget.fields import (
    AccountChildrenFilteredQuerysetPKField,
    SubAccountChildrenFilteredQuerysetPKField,
)
from greenbudget.app.subaccount.models import BudgetSubAccount

from .models import Markup, BudgetAccountMarkup, BudgetSubAccountMarkup


class MarkupSerializer(ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    identifier = serializers.CharField(
        required=False,
        allow_blank=False,
        allow_null=True,
        trim_whitespace=False
    )
    description = serializers.CharField(
        required=False,
        allow_blank=False,
        allow_null=True,
        trim_whitespace=False
    )
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)
    updated_by = serializers.PrimaryKeyRelatedField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    rate = serializers.FloatField(required=False, allow_null=True)
    unit = ModelChoiceField(
        required=False,
        choices=Markup.UNITS,
        allow_null=True
    )

    class Meta:
        model = Markup
        fields = (
            'id', 'identifier', 'description', 'created_by', 'created_at',
            'updated_by', 'updated_at', 'rate', 'unit')

    def validate_children(self, children):
        request = self.context['request']
        if request.method == "POST" and len(children) == 0:
            raise exceptions.ValidationError(
                "A markup instance cannot be created with no children.")
        return children

    def update(self, *args, **kwargs):
        """
        Overridden to perform cleanup of empty :obj:`Markup` instances.

        When a :obj:`Markup` is updated by setting it's `children` to an empty
        list, we want to perform cleanup and remove the empty :obj:`Markup that
        no longer has any children.

        This cannot be accomplished with the @signals.model with a listener
        for a field change because @signals.model cannot track field changes
        for M2M fields (at least not now).

        TODO:
        ----
        We should investigate whether or not there is a better way around this
        problem.  At the very least, we should develop CRON tasks that should
        remove remnant empty groups.
        """
        instance = super().update(*args, **kwargs)
        if instance.children.count() == 0:
            instance.delete()
        return instance


class BudgetAccountMarkupSerializer(MarkupSerializer):
    children = AccountChildrenFilteredQuerysetPKField(
        many=True,
        required=True,
        queryset=BudgetAccount.objects.all()
    )

    class Meta(MarkupSerializer.Meta):
        model = BudgetAccountMarkup
        fields = MarkupSerializer.Meta.fields + ('children', )


class BudgetSubAccountMarkupSerializer(MarkupSerializer):
    children = SubAccountChildrenFilteredQuerysetPKField(
        many=True,
        required=True,
        queryset=BudgetSubAccount.objects.all()
    )

    class Meta(MarkupSerializer.Meta):
        model = BudgetSubAccountMarkup
        fields = MarkupSerializer.Meta.fields + ('children', )
