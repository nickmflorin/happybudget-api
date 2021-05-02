from rest_framework import serializers, exceptions

from greenbudget.lib.rest_framework_utils.serializers import (
    EnhancedModelSerializer)

from greenbudget.app.account.models import BudgetAccount, TemplateAccount
from greenbudget.app.tagging.serializers import ColorField
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

    color_new = ColorField(content_type_model=Group)

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
            'updated_at', 'color', 'estimated', 'color_new')

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

    def create(self, *args, **kwargs):
        """
        Overridden to perform cleanup of empty :obj:`Group` instances.

        When a :obj:`Group` is created, it can be created with children that
        already belong to another :obj:`Group`.  When this happens, the children
        are removed from the other :obj:`Group` and included in the new
        :obj:`Group`.  We want to perform cleanup, and remove empty :obj:`Group`
        instances that have no children.

        This is partially accomplished with :obj:`track_model`.  However, when
        the above situation occurs, the :obj:`track_model` will not work,
        because both of these implementations will fail:

        (1) :obj:`track_model` on :obj:`Group`

        @track_model(on_field_change_hooks={'parent': remove_empty_groups})
        class BudgetAccountGroup(Group):
            ...
            parent = models.ForeignKey(
                to='budget.Budget',
                ...
            )

        The mechanics of :obj:`track_model` responsible for removing the
        :obj:`Group` if it has no more children will not be triggered because
        :obj:`track_model` will only trigger when the :obj:`Group` with no more
        children itself is updated.  In this situation, we are not updating the
        :obj:`Group` that has no more children, we are updating the new
        :obj:`Group` that will have the children that previously existed on the
        old :obj:`Group`.

        (2) :obj:`track_model` on :obj:`Account` or :obj:`SubAccount`

        class BudgetAccountGroup(Group):
            ...
            parent = models.ForeignKey(
                to='budget.Budget',
                ...
            )

        @track_model(on_field_change_hooks={'group': remove_empty_groups})
        class BudgetAccount(Account):
            group = models.ForeignKey(
                to='group.BudgetAccountGroup',
                related_name='children'
            )

        Here, we cannot use the :obj:`track_model` on the :obj:`Account` or
        :obj:`SubAccount` models to remove empty groups after the group assigned
        to those models changes because for DRF we are updating the models via
        the `children` attribute, which is the reverse FK accessor, and
        apparently that does not trigger the post_save hooks on the primary
        model:

        PATCH /v1/groups/<pk>/ { children: [...] } -> Updating the `children`
        on the :obj:`BudgetAccountGroup` (i.e. updating a reverse FK accessor)
        will not trigger the `post_save` on :obj:`BudgetAccount`.

        For the above reason, we need to address this problem without the
        :obj:`track_model` behavior.

        (3) `post_save` signals directly on :obj:`Group`

        We cannot accomplish this at the database level (or model level) via
        post_save signals.  Consider we try to accomplish this with the
        following signal:

        @dispatch.receiver(post_save, sender=BudgetSubAccountGroup)
        def remove_empty_groups(instance, **kwargs):
            for sibling_group in instance.parent.groups.all():
                if sibling_group.children.count() == 0:
                    sibling_group.delete()

        If we were to do this, we would run into issues creating instances of
        :obj:`Group`.  Since the `children` field is a reverse FK accessor,
        the :obj:`Group` has to be created before an entity can be assigned
        a group.  That means a :obj:`Group` will at times have no children just
        before children are assigned - and we cannot have those groups incident-
        ally deleted before children are assigned.

        For this reason, we need to accomplish this behavior at the request/
        response interface - which is why we override this method here.

        TODO:
        ----
        We should investigate whether or not there is a better way around this
        problem.  At the very least, we should develop CRON tasks that should
        remove remnant empty groups.
        """
        instance = super().create(*args, **kwargs)
        for sibling_group in instance.parent.groups.all():
            if sibling_group != instance \
                    and sibling_group.children.count() == 0:
                sibling_group.delete()
        return instance

    def update(self, *args, **kwargs):
        """
        Overridden to perform cleanup of empty :obj:`Group` instances.  See
        docstring in `.create()` method for a more detailed explanation.
        """
        instance = super().update(*args, **kwargs)

        siblings = [
            sib for sib in instance.parent.groups.all()
            if sib != instance
        ]
        for sibling_group in siblings:
            if sibling_group.children.count() == 0:
                sibling_group.delete()
        return instance


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
        required=True,
        queryset=BudgetAccount.objects.active()
    )

    class Meta(GroupSerializer.Meta):
        model = BudgetAccountGroup
        fields = GroupSerializer.Meta.fields + (
            'children', 'actual', 'variance')


class TemplateAccountGroupSerializer(AbstractAccountGroupSerializer):
    children = serializers.PrimaryKeyRelatedField(
        many=True,
        required=True,
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
        required=True,
        queryset=BudgetSubAccount.objects.active()
    )

    class Meta(GroupSerializer.Meta):
        model = BudgetSubAccountGroup
        fields = GroupSerializer.Meta.fields + (
            'children', 'actual', 'variance')


class TemplateSubAccountGroupSerializer(AbstractSubAccountGroupSerializer):
    children = serializers.PrimaryKeyRelatedField(
        many=True,
        required=True,
        queryset=TemplateSubAccount.objects.active()
    )

    class Meta(GroupSerializer.Meta):
        model = TemplateSubAccountGroup
        fields = GroupSerializer.Meta.fields + ('children', )
