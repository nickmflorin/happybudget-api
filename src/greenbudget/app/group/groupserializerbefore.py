from rest_framework import serializers, exceptions

from greenbudget.lib.rest_framework_utils.serializers import (
    EnhancedModelSerializer)

from greenbudget.app.account.models import BudgetAccount, TemplateAccount
from greenbudget.app.subaccount.models import (
    BudgetSubAccount, TemplateSubAccount)

from .models import (
    Group,
    BudgetAccountGroup,
    TemplateAccountGroup,
    BudgetSubAccountGroup,
    TemplateSubAccountGroup
)


class GroupSerializer(EnhancedModelSerializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(
        required=False,
        allow_blank=False,
        allow_null=False
    )
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)
    updated_by = serializers.PrimaryKeyRelatedField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    estimated = serializers.FloatField(read_only=True)
    color = serializers.ChoiceField(
        required=True,
        choices=[
            "#797695",
            "#ff7165",
            "#80cbc4",
            "#ce93d8",
            "#fed835",
            "#c87987",
            "#69f0ae",
            "#a1887f",
            "#81d4fa",
            "#f75776",
            "#66bb6a",
            "#58add6"
        ]
    )

    class Meta:
        model = Group
        fields = (
            'id', 'name', 'created_by', 'created_at', 'updated_by',
            'updated_at', 'color', 'estimated')

    def validate_name(self, value):
        parent = self.context.get('parent')
        if parent is None:
            parent = self.instance.parent
        validator = serializers.UniqueTogetherValidator(
            queryset=parent.groups.all(),
            fields=('name', ),
        )
        validator({'name': value}, self)
        return value


class AbstractAccountGroupSerializer(GroupSerializer):
    class Meta:
        abstract = True

    def validate_children(self, value):
        parent = self.context.get('parent')
        if parent is None:
            parent = self.instance.parent
        for child in value:
            if child.budget != parent:
                raise exceptions.ValidationError(
                    "The %s %s does not belong to the same %s "
                    "that the Group does (%s)." % (
                        type(child).__name__, child.pk, type(parent).__name__,
                        parent.pk)
                )
        return value


class BudgetAccountGroupSerializer(AbstractAccountGroupSerializer):
    actual = serializers.FloatField(read_only=True)
    variance = serializers.FloatField(read_only=True)
    children = serializers.PrimaryKeyRelatedField(
        many=True,
        required=False,
        queryset=BudgetAccount.objects.active()
    )

    class Meta(GroupSerializer.Meta):
        model = BudgetAccountGroup
        fields = GroupSerializer.Meta.fields + (
            'children', 'actual', 'variance')


class TemplateAccountGroupSerializer(AbstractAccountGroupSerializer):
    children = serializers.PrimaryKeyRelatedField(
        many=True,
        required=False,
        queryset=TemplateAccount.objects.active()
    )

    class Meta(GroupSerializer.Meta):
        model = TemplateAccountGroup
        fields = GroupSerializer.Meta.fields + ('children', )


class AbstractSubAccountGroupSerializer(GroupSerializer):
    class Meta:
        abstract = True

    def validate_children(self, value):
        parent = self.context.get('parent')
        if parent is None:
            parent = self.instance.parent
        for child in value:
            if child.parent != parent:
                raise exceptions.ValidationError(
                    "The %s %s does not belong to the same %s "
                    "that the Group does (%s)." % (
                        type(child).__name__, child.pk, type(parent).__name__,
                        parent.pk)
                )
            # Is this check necessary?  Would this otherwise be constrained
            # by model restrictions?
            elif child.budget != parent.budget:
                raise exceptions.ValidationError(
                    "The %s %s does not belong to the same %s "
                    "that the Group does (%s)." % (
                        type(child).__name__, child.pk,
                        type(child.budget).__name__, parent.pk)
                )
        return value


class BudgetSubAccountGroupSerializer(AbstractSubAccountGroupSerializer):
    actual = serializers.FloatField(read_only=True)
    variance = serializers.FloatField(read_only=True)
    children = serializers.PrimaryKeyRelatedField(
        many=True,
        required=False,
        queryset=BudgetSubAccount.objects.active()
    )

    class Meta(GroupSerializer.Meta):
        model = BudgetSubAccountGroup
        fields = GroupSerializer.Meta.fields + (
            'children', 'actual', 'variance')


class TemplateSubAccountGroupSerializer(AbstractSubAccountGroupSerializer):
    children = serializers.PrimaryKeyRelatedField(
        many=True,
        required=False,
        queryset=TemplateSubAccount.objects.active()
    )

    class Meta(GroupSerializer.Meta):
        model = TemplateSubAccountGroup
        fields = GroupSerializer.Meta.fields + ('children', )
