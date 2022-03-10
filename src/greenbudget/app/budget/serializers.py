from rest_framework import serializers

from greenbudget.app import exceptions
from greenbudget.app.account.serializers import AccountPdfSerializer
from greenbudget.app.authentication.serializers import PublicTokenSerializer
from greenbudget.app.group.serializers import GroupSerializer
from greenbudget.app.io.fields import Base64ImageField
from greenbudget.app.markup.serializers import MarkupSerializer
from greenbudget.app.template.models import Template

from .models import BaseBudget, Budget


class BaseBudgetSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(
        required=True,
        allow_blank=False,
        allow_null=False
    )
    type = serializers.CharField(read_only=True)
    domain = serializers.CharField(read_only=True)

    class Meta:
        model = BaseBudget
        fields = ('id', 'name', 'type', 'domain')


class BudgetPdfSerializer(BaseBudgetSerializer):
    type = serializers.CharField(read_only=True, source='pdf_type')
    children = AccountPdfSerializer(many=True, read_only=True)
    groups = GroupSerializer(many=True, read_only=True)
    children_markups = MarkupSerializer(many=True, read_only=True)
    nominal_value = serializers.FloatField(read_only=True)
    accumulated_fringe_contribution = serializers.FloatField(read_only=True)
    accumulated_markup_contribution = serializers.FloatField(read_only=True)
    actual = serializers.FloatField(read_only=True)

    class Meta:
        model = Budget
        fields = ('children', 'groups', 'children_markups') \
            + BaseBudgetSerializer.Meta.fields \
            + (
                'nominal_value', 'actual', 'accumulated_markup_contribution',
                'accumulated_fringe_contribution'
        )
        read_only_fields = fields


class BudgetSimpleSerializer(BaseBudgetSerializer):
    updated_at = serializers.DateTimeField(read_only=True)
    image = Base64ImageField(required=False, allow_null=True)
    template = serializers.PrimaryKeyRelatedField(
        write_only=True,
        required=False,
        queryset=Template.objects.all(),
        allow_null=False
    )

    class Meta:
        model = Budget
        fields = BaseBudgetSerializer.Meta.fields + (
            'updated_at', 'template', 'image')

    def create(self, validated_data):
        if 'template' not in validated_data:
            return super().create(validated_data)
        template = validated_data.pop('template')
        if 'created_by' in validated_data:
            del validated_data['created_by']
        request = self.context['request']
        return Template.objects.derive(template, request.user, **validated_data)

    def validate_template(self, template):
        request = self.context['request']
        if not request.user.is_staff:
            if not template.created_by.is_staff \
                    and template.created_by != request.user:
                raise exceptions.ValidationError(
                    message="Do not have permission to use template.")
        return template

    def to_representation(self, instance):
        # We allow unauthenticated users to retrieve information about a
        # Budget that is associated with a PublicToken.  In this case, we cannot
        # include whether or not the Budget is permissioned, both because the
        # user is anonymous and we would not want to include that info in a
        # response.
        data = super().to_representation(instance)
        if self.context['user'].is_authenticated:
            assert instance.created_by == self.context['user'], \
                f"Attempting to access budget {instance.pk} created by user " \
                f"{instance.created_by.id} as logged in user " \
                f"{self.context['user'].pk}!"
            data['is_permissioned'] = False
            if not self.context['user'].has_product('__any__'):
                data['is_permissioned'] = not instance.is_first_created
        return data


class BudgetSerializer(BudgetSimpleSerializer):
    nominal_value = serializers.FloatField(read_only=True)
    accumulated_fringe_contribution = serializers.FloatField(read_only=True)
    accumulated_markup_contribution = serializers.FloatField(read_only=True)
    actual = serializers.FloatField(read_only=True)
    public_token = PublicTokenSerializer(read_only=True)

    class Meta:
        model = Budget
        fields = BudgetSimpleSerializer.Meta.fields \
            + ('nominal_value', 'actual', 'public_token',
                'accumulated_markup_contribution',
                'accumulated_fringe_contribution'
            )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        assert 'user' in self.context, \
            "The context must be provided to this serializer when serializing " \
            "instances."
        if not self.context['user'].is_authenticated:
            del data['public_token']
        return data
