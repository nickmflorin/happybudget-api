from rest_framework import serializers

from happybudget.app import exceptions
from happybudget.app.account.serializers import AccountPdfSerializer
from happybudget.app.actual.models import Actual
from happybudget.app.authentication.serializers import PublicTokenSerializer
from happybudget.app.group.serializers import GroupSerializer
from happybudget.app.io.fields import Base64ImageField
from happybudget.app.markup.serializers import MarkupSerializer
from happybudget.app.serializers import ModelSerializer
from happybudget.app.template.models import Template
from happybudget.app.user.fields import UserTimezoneAwareDateField
from happybudget.app.user.serializers import SimpleUserSerializer

from .models import BaseBudget, Budget


class BaseBudgetSerializer(ModelSerializer):
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

        # These values cannot be included in the derivation because they are
        # related to the users that created and updated the Budget we are
        # deriving.
        for fld in ('created_by', 'updated_by'):
            if fld in validated_data:
                del validated_data[fld]
        return Template.objects.derive(template, self.user, **validated_data)

    def validate_template(self, template):
        if not self.user.is_staff and not template.user_owner.is_staff \
                and template.user_owner != self.user:
            raise exceptions.ValidationError(
                "User does not have permission to use template.")
        return template

    def to_representation(self, instance):
        # We allow unauthenticated users to retrieve information about a
        # Budget that is associated with a PublicToken.  In this case, we cannot
        # include whether or not the Budget is permissioned, both because the
        # user is anonymous and we would not want to include that info in a
        # response.
        data = super().to_representation(instance)
        data['updated_by'] = SimpleUserSerializer(
            instance=instance.updated_by).data
        if self.user.is_authenticated and instance.user_owner == self.user:
            data['is_permissioned'] = False
            if not self.user.has_product('__any__'):
                data['is_permissioned'] = not instance.is_first_created
        return data


class BudgetSerializer(BudgetSimpleSerializer):
    nominal_value = serializers.FloatField(read_only=True)
    accumulated_fringe_contribution = serializers.FloatField(read_only=True)
    accumulated_markup_contribution = serializers.FloatField(read_only=True)
    actual = serializers.FloatField(read_only=True)
    public_token = PublicTokenSerializer(read_only=True)
    archived = serializers.BooleanField(write_only=True, required=False)

    class Meta(BudgetSimpleSerializer.Meta):
        fields = BudgetSimpleSerializer.Meta.fields \
            + ('nominal_value', 'actual', 'public_token', 'archived',
                'accumulated_markup_contribution',
                'accumulated_fringe_contribution'
            )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if not self.user.is_authenticated:
            del data['public_token']
        return data


class BulkImportBudgetActualsSerializer(ModelSerializer):
    start_date = UserTimezoneAwareDateField(allow_null=False, required=True)
    end_date = UserTimezoneAwareDateField(
        allow_null=False,
        required=False,
        default_today=True
    )
    source = serializers.ChoiceField(choices=Actual.IMPORT_SOURCES)
    public_token = serializers.CharField(
        required=True,
        allow_null=False,
        allow_blank=False
    )
    account_ids = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )

    class Meta:
        model = Budget
        fields = (
            'start_date', 'end_date', 'source', 'public_token', 'account_ids')

    def validate(self, attrs):
        # Since the end_date can default to today, it is more appropriate to
        # raise the exception relevant to the `start_date` field, since that
        # will always be provided by the user.
        if attrs['start_date'] >= attrs['end_date']:
            raise exceptions.InvalidFieldError('start_date', message=(
                "The start date must be in the past and before the end date."))
        return attrs

    def update(self, budget, validated_data):
        actuals = Actual.objects.bulk_import(
            created_by=self.user,
            updated_by=self.user,
            budget=budget,
            raise_exception=True,
            **validated_data
        )
        budget.refresh_from_db()
        return budget, actuals
