from rest_framework import serializers, exceptions

from greenbudget.lib import drf

from greenbudget.app.budgeting.fields import TableChildrenPrimaryKeyRelatedField
from greenbudget.app.budgeting.serializers import EntitySerializer
from greenbudget.app.contact.models import Contact
from greenbudget.app.fringe.models import Fringe
from greenbudget.app.group.models import Group
from greenbudget.app.group.serializers import GroupSerializer
from greenbudget.app.tagging.fields import TagField
from greenbudget.app.tagging.serializers import TagSerializer, ColorSerializer
from greenbudget.app.user.fields import UserFilteredQuerysetPKField

from .models import (
    SubAccount, BudgetSubAccount, TemplateSubAccount, SubAccountUnit)


class SubAccountUnitSerializer(TagSerializer):
    color = ColorSerializer(read_only=True)

    class Meta:
        model = SubAccountUnit
        fields = TagSerializer.Meta.fields + ("color", )


class SubAccountSimpleSerializer(drf.serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    type = serializers.CharField(read_only=True)
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

    class Meta:
        model = SubAccount
        fields = ('id', 'identifier', 'type', 'description')


class SubAccountTreeNodeSerializer(SubAccountSimpleSerializer):
    children = serializers.PrimaryKeyRelatedField(
        queryset=BudgetSubAccount.objects.all()
    )

    class Meta:
        model = SubAccount
        fields = SubAccountSimpleSerializer.Meta.fields + ('children', )

    def __init__(self, *args, **kwargs):
        # The subset is the set of SubAccount(s) that have been filtered by
        # the search.  Only these SubAccount(s) will be included as children
        # to each node of the tree.
        self._subset = kwargs.pop('subset')
        self._search_path = kwargs.pop('search_path')
        super().__init__(*args, **kwargs)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data.update(
            in_search_path=instance in self._search_path,
            children=[
                self.__class__(
                    instance=child,
                    search_path=self._search_path,
                    subset=self._subset
                ).data
                for child in self._subset if child.parent == instance
            ]
        )
        return data


class SubAccountSerializer(SubAccountSimpleSerializer):
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)
    updated_by = serializers.PrimaryKeyRelatedField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    quantity = serializers.IntegerField(
        required=False,
        allow_null=True
    )
    rate = serializers.FloatField(required=False, allow_null=True)
    multiplier = serializers.FloatField(required=False, allow_null=True)
    estimated = serializers.FloatField(read_only=True)
    fringe_contribution = serializers.FloatField(read_only=True)
    markup_contribution = serializers.FloatField(read_only=True)
    actual = serializers.FloatField(read_only=True)
    group = TableChildrenPrimaryKeyRelatedField(
        obj_name='Sub Account',
        required=False,
        allow_null=True,
        child_instance_cls=lambda parent: Group.child_instance_cls_for_parent(
            parent),
        write_only=True,
    )
    unit = TagField(
        serializer_class=SubAccountUnitSerializer,
        queryset=SubAccountUnit.objects.all(),
        required=False,
        allow_null=True
    )
    children = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    object_id = serializers.IntegerField(read_only=True)
    parent_type = serializers.ChoiceField(
        choices=["account", "subaccount"],
        read_only=True
    )
    fringes = serializers.PrimaryKeyRelatedField(
        many=True,
        required=False,
        queryset=Fringe.objects.all()
    )
    contact = UserFilteredQuerysetPKField(
        required=False,
        allow_null=True,
        queryset=Contact.objects.all(),
        user_field='user'
    )

    class Meta:
        model = SubAccount
        fields = SubAccountSimpleSerializer.Meta.fields + (
            'identifier', 'created_by', 'updated_by', 'created_at',
            'updated_at', 'quantity', 'rate', 'multiplier', 'unit', 'object_id',
            'parent_type', 'estimated', 'children', 'fringes', 'contact',
            'fringe_contribution', 'markup_contribution', 'actual', 'group')

    def validate(self, attrs):
        if self.instance is not None and self.instance.children.count() != 0:
            if any([field in attrs for field in self.instance.DERIVING_FIELDS]):
                raise exceptions.ValidationError(
                    "Field can only be updated when the sub account is not "
                    "derived."
                )
        return super().validate(attrs)


class BudgetSubAccountSerializer(SubAccountSerializer):
    class Meta:
        model = BudgetSubAccount
        fields = SubAccountSerializer.Meta.fields


class BudgetSubAccountDetailSerializer(BudgetSubAccountSerializer):
    ancestors = EntitySerializer(many=True, read_only=True)
    siblings = EntitySerializer(many=True, read_only=True)

    class Meta:
        model = BudgetSubAccount
        fields = BudgetSubAccountSerializer.Meta.fields + (
            'ancestors', 'siblings')


class TemplateSubAccountSerializer(SubAccountSerializer):
    class Meta:
        model = TemplateSubAccount
        fields = SubAccountSerializer.Meta.fields


class TemplateSubAccountDetailSerializer(TemplateSubAccountSerializer):
    ancestors = EntitySerializer(many=True, read_only=True)
    siblings = EntitySerializer(many=True, read_only=True)

    class Meta:
        model = TemplateSubAccount
        fields = TemplateSubAccountSerializer.Meta.fields + (
            'ancestors', 'siblings')


class SubAccountPdfSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    type = serializers.CharField(read_only=True)
    identifier = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)
    quantity = serializers.IntegerField(read_only=True)
    rate = serializers.FloatField(read_only=True)
    multiplier = serializers.FloatField(read_only=True)
    estimated = serializers.FloatField(read_only=True)
    fringe_contribution = serializers.FloatField(read_only=True)
    markup_contribution = serializers.FloatField(read_only=True)
    unit = TagField(
        model_cls=SubAccountUnit,
        read_only=True,
        serializer_class=SubAccountUnitSerializer
    )
    contact = UserFilteredQuerysetPKField(
        required=False,
        allow_null=True,
        queryset=Contact.objects.all(),
        user_field='user'
    )
    children = serializers.SerializerMethodField()
    groups = GroupSerializer(many=True, read_only=True)

    class Meta:
        model = BudgetSubAccount
        fields = ('id', 'identifier', 'description', 'quantity', 'rate',
            'multiplier', 'estimated', 'unit', 'children', 'contact',
            'groups', 'type', 'fringe_contribution', 'markup_contribution')
        read_only_fields = fields

    def get_children(self, instance):
        return self.__class__(instance.children.all(), many=True).data
