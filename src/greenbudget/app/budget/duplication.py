import collections
import contextlib
import logging
import json

from django.contrib.contenttypes.models import ContentType
from django.db import models

from greenbudget.app import signals


logger = logging.getLogger('greenbudget')


DISALLOWED_ATTRIBUTES = [('editable', False), ('primary_key', True)]
DISALLOWED_FIELD_NAMES = ['id', 'object_id']
DISALLOWED_FIELDS = [
    models.fields.AutoField,
    models.ManyToManyField,
    models.ForeignKey,
    models.OneToOneField,
    models.ImageField,
    models.FileField
]


def field_can_be_duplicated(field):
    if field.name in DISALLOWED_FIELD_NAMES:
        return False
    for attr_set in DISALLOWED_ATTRIBUTES:
        if getattr(field, attr_set[0], None) is attr_set[1]:
            return False
    if type(field) in DISALLOWED_FIELDS:
        return False
    elif type(field) in (models.fields.DateTimeField, models.fields.DateField):
        if field.auto_now_add is True or field.auto_now is True:
            return False
        return True
    return True


def instantiate_duplicate(instance, user, **overrides):
    kwargs = {}
    destination_cls = overrides.pop('destination_cls', type(instance))
    for field_obj in type(instance)._meta.fields:
        if field_can_be_duplicated(field_obj) \
                and field_obj in destination_cls._meta.fields \
                and field_obj.name not in overrides:
            kwargs[field_obj.name] = getattr(instance, field_obj.name)
    if hasattr(instance.__class__, 'created_by'):
        kwargs['created_by'] = user
    if hasattr(instance.__class__, 'updated_by'):
        kwargs['updated_by'] = user
    return destination_cls(**kwargs, **overrides)


class ObjectRelationship:
    def __init__(self, instance, original, created=False, saved=False,
            update_fields=None):
        self.instance = instance
        self.original = original
        self.created = created
        self.saved = saved
        self.update_fields = update_fields or set([])

    @property
    def original_pk(self):
        return self.original.pk

    @property
    def new_pk(self):
        if self.instance.pk is None:
            raise Exception("Instance has not been saved yet!")
        return self.instance.pk

    @property
    def serialized(self):
        return {
            'instance': "%s" % self.instance,
            'original': "%s" % self.original,
            'created': self.created,
            'saved': self.saved,
            'update_fields': self.update_fields
        }

    def __str__(self):
        return "%s" % self.serialized


class AssociatedObjectNotFound(KeyError):
    def __init__(self, model_cls, pk):
        self.model_cls = model_cls
        self.pk = pk

    def __str__(self):
        return (
            "Could not find associated %s instance for PK %s."
            % (self.model_cls.__name__, self.pk)
        )


class ObjectSet(collections.abc.Mapping):
    bulk_create_kwargs = {}

    def __init__(self, model_cls, user):
        self.user = user
        self.model_cls = model_cls
        # Data that stores a mapping of original model PKs to the associated
        # DuplicatedInstance.
        self._data = {}

    @contextlib.contextmanager
    def transaction(self):
        try:
            yield self
        finally:
            self.clear()

    def __iter__(self):
        return self._data.__iter__()

    def __getitem__(self, pk):
        try:
            return self._data.__getitem__(pk)
        except KeyError:
            raise AssociatedObjectNotFound(self.model_cls, pk)

    @property
    def serialized(self):
        data = {}
        for k, v in self._data.items():
            data[k] = str(v)
        return data

    def __str__(self):
        return json.dumps(self.serialized)

    def __setitem__(self, k, v):
        if k in self._data:
            raise KeyError(
                "Duplicated %s instance already exists for PK %s."
                % (self.model_cls.__name__, k)
            )
        self._data.__setitem__(k, v)

    def __len__(self):
        return self._data.__len__()

    def __delitem__(self, k):
        return self._data.__delitem__(k)

    def modify(self, pk, **kwargs):
        """
        Modifies the duplicated instance associated with the primary key
        value provided as `pk`.  The attributes provided as keyword arguments
        will be applied to the duplicated instance stored in the mapped data
        associated with the `pk` value.
        """
        instance = self[pk]
        for k, v in kwargs.items():
            setattr(instance.instance, k, v)
            # Denote the instance as requiring a save so that we know which
            # instances to include in the next bulk_update operation.
            instance.saved = False
            # Keep track of the fields updated for each instance so we can
            # include them in the bulk_update operation.
            instance.update_fields.add(k)

    def instantiate_duplicate(self, obj, **overrides):
        return instantiate_duplicate(
            instance=obj,
            user=self.user,
            destination_cls=self.model_cls,
            **overrides
        )

    @classmethod
    def from_join(cls, instances):
        """
        Creates a new :obj:`ObjectSet` instance by combining the data of several
        other :obj:`ObjectSet` instances, where the :obj:`ObjectSet` instances
        must be of the same form (same `user` and `model_cls` properties).
        """
        assert len(instances) != 0, "Must provide at least one instance to join."
        object_set = cls(
            model_cls=instances[0].model_cls,
            user=instances[0].user
        )
        for instance in instances:
            object_set.join(instance)
        return object_set

    def join(self, other):
        """
        Merges the data of the :obj:`ObjectSet` instance with another
        :obj:`ObjectSet` instance.
        """
        assert self.user == other.user and self.model_cls is other.model_cls, \
            "Cannot join two object sets that have different properties for " \
            "`model_cls` and `user`."
        for k, _ in other._data.items():
            if k in self._data:
                raise Exception(
                    "Cannot join two object sets that each have references to "
                    "the same key `%s`." % k
                )
            self._data[k] = other._data[k]

    def add(self, obj, **overrides):
        """
        Adds a new already-created instance to the set, creating it's associated
        duplicated version and associating them in a :obj:`ObjectRelationship`
        instance.
        """
        strict = overrides.pop('strict', True)
        if obj.pk not in self:
            self[obj.pk] = ObjectRelationship(
                instance=self.instantiate_duplicate(obj, **overrides),
                original=obj
            )
        elif strict:
            raise Exception('Relationship already exists for PK %s.' % obj.pk)

    def clear(self):
        # Isolate the instances that have been created but have not been saved
        # (due to changes since the last save or the first create) so they can
        # be bulk updated.
        not_saved = [
            (k, v) for k, v in self.items()
            if not v.saved and v.created
        ]
        # Isolate the instances that have not been created yet so they can be
        # bulk created in one batch.
        not_created = [
            (k, v) for k, v in self.items()
            if not v.created
        ]
        # Only remove the non-created instances from the relationships because
        # those have to be replaced with relationships that have PKs for the
        # duplicated instance.
        self._data = {k: v for k, v in self.items() if v.created}
        if not_created:
            instances = [ns[1].instance for ns in not_created]
            if instances:
                created = self.model_cls.objects.bulk_create(
                    instances,
                    **self.bulk_create_kwargs
                )
                assert len(created) == len(not_created), \
                    "Suspicious query result: Bulk create tried to create %s " \
                    "instances, but returned %s instances." \
                    % (len(not_created), len(created))

                # Add the newly created instances back into the data,
                # attributing them as having been saved and created.
                self._data.update({
                    not_created[i][0]: ObjectRelationship(
                        instance=created[i],
                        created=True,
                        saved=True,
                        original=not_created[i][1].original,
                        update_fields=set([])
                    )
                    for i in range(len(created))
                })
        if not_saved:
            assert all([len(ns[1].update_fields) != 0 for ns in not_saved])

            update_fields = set([])
            for instance in [ns[1] for ns in not_saved]:
                update_fields.update(instance.update_fields)

            instances = [ns[1].instance for ns in not_saved]
            if instances:
                self.model_cls.objects.bulk_update(
                    instances, tuple(update_fields))

                # Update the instances post bulk_update to denote that they do
                # not need to be saved anymore and do not have any more changed
                # fields.
                for _, v in self.items():
                    v.saved = True
                    v.update_fields = []


class ConcreteObjectSet(ObjectSet):
    bulk_create_kwargs = {'predetermine_pks': True}


class PolymorphicObjectSet(ObjectSet):
    bulk_create_kwargs = {'return_created_objects': True}


@signals.disable()
def duplicate(
    budget,
    user,
    destination_cls=None,
    destination_account_cls=None,
    destination_subaccount_cls=None,
    **overrides
):
    from greenbudget.app.account.models import Account
    from greenbudget.app.actual.models import Actual
    from greenbudget.app.budget.models import BaseBudget
    from greenbudget.app.fringe.models import Fringe
    from greenbudget.app.group.models import Group
    from greenbudget.app.markup.models import Markup
    from greenbudget.app.subaccount.models import SubAccount

    source_cls = type(budget)
    destination_cls = destination_cls or source_cls
    source_budget_ct = ContentType.objects.get_for_model(source_cls)
    dest_budget_ct = ContentType.objects.get_for_model(destination_cls)

    markup_ct = ContentType.objects.get_for_model(Markup)

    source_a_cls = budget.account_cls
    dest_a_cls = destination_account_cls or source_a_cls
    source_a_ct = ContentType.objects.get_for_model(source_a_cls)
    dest_a_ct = ContentType.objects.get_for_model(dest_a_cls)

    source_sa_cls = budget.subaccount_cls
    dest_sa_cls = destination_subaccount_cls or source_sa_cls
    source_sa_ct = ContentType.objects.get_for_model(source_sa_cls)
    dest_sa_ct = ContentType.objects.get_for_model(dest_sa_cls)

    duplicated_budget = instantiate_duplicate(
        instance=budget,
        user=user,
        destination_cls=destination_cls,
        **overrides
    )
    duplicated_budget.save()

    accounts = PolymorphicObjectSet(
        model_cls=dest_a_ct.model_class(),
        user=user
    )
    with accounts.transaction():
        for account in source_a_ct.model_class().objects.filter(parent=budget):
            accounts.add(account, parent=duplicated_budget)

    subaccounts = PolymorphicObjectSet(
        model_cls=dest_sa_ct.model_class(),
        user=user
    )

    subs_by_level = {}
    for sub in source_sa_ct.model_class().objects.filter_by_budget(budget) \
            .select_related('content_type'):
        subs_by_level.setdefault(
            sub.nested_level,
            PolymorphicObjectSet(
                model_cls=dest_sa_ct.model_class(),
                user=user
            )
        )
        # Note: We do not add the parents to the SubAccount instances until
        # the parents for each level of the tree can be created before the
        # SubAccount(s) in the next level of the tree are created.
        subs_by_level[sub.nested_level].add(sub)

    # Make sure the the numeric keys of the subaccounts (indexed by level) are
    # consecutive (i.e {0: [...], 1: [...] })
    for i in range(len(subs_by_level.keys())):
        assert i in subs_by_level

    if subs_by_level:
        for level in range(len(subs_by_level)):
            subaccounts_set = subs_by_level[level]
            if level == 0:
                for k, v in subaccounts_set.items():
                    parent = accounts[v.original.object_id]
                    assert parent.created, \
                        "The original instance was not created!"
                    subaccounts_set.modify(k,
                        object_id=parent.instance.pk,
                        content_type_id=dest_a_ct.pk
                    )
            else:
                # Clear the SubAccount(s) at the previous level because those
                # SubAccount(s) will need to be referenced as parents of the
                # SubAccount(s) at this level.
                subs_by_level[level - 1].clear()
                for k, v in subaccounts_set.items():
                    parent = subs_by_level[level - 1][v.original.object_id]
                    assert parent.created, \
                        "The original instance was not created!"
                    subaccounts_set.modify(k,
                        object_id=parent.instance.pk,
                        content_type_id=dest_sa_ct.pk
                    )
        # Save/clear the leftover or last level of SubAccount(s) in the tree.
        subs_by_level[len(subs_by_level) - 1].clear()

        # Flatten all of the subaccount levels together into one object set.
        subaccounts = PolymorphicObjectSet.from_join(
            list(subs_by_level.values()))

    # Duplicate the Group instances associated with the Budget, Account and
    # SubAccount instances.
    groups = ConcreteObjectSet(model_cls=Group, user=user)
    with groups.transaction():
        for group in Group.objects.filter_by_budget(budget) \
                .select_related('content_type') \
                .prefetch_related('accounts', 'subaccounts'):
            model_cls = group.content_type.model_class()
            assert issubclass(model_cls, (BaseBudget, Account, SubAccount))
            if issubclass(model_cls, BaseBudget):
                groups.add(group,
                    content_type_id=dest_budget_ct.pk,
                    object_id=duplicated_budget.pk
                )
            elif issubclass(model_cls, Account):
                groups.add(group,
                    content_type_id=dest_a_ct.pk,
                    object_id=accounts[group.object_id].new_pk
                )
            else:
                groups.add(group,
                    content_type_id=dest_sa_ct.pk,
                    object_id=subaccounts[group.object_id].new_pk
                )

    # Associate the newly duplicated Group instances with the already duplicated
    # Account/SubAccount instances.
    for k, v in groups.items():
        for account in v.original.accounts.all():
            try:
                accounts.modify(account.pk, group_id=v.instance.pk)
            except AssociatedObjectNotFound:
                # This seems to fail often, so until we get to the bottom of it
                # we should add additional logging.
                logger.error(
                    "Could not update group for new account associated with "
                    "%s (PK = %s) as it could not be found."
                    % (accounts.model_cls.__name__, account.pk), extra={
                        'pk': account.pk,
                        'model_cls': accounts.model_cls.__name__,
                        'accounts': str(accounts),
                        'group_id': k,
                        'group_accounts': [
                            a.pk for a in v.original.accounts.all()]

                    }
                )
        for subaccount in v.original.subaccounts.all():
            try:
                # This seems to fail often, so until we get to the bottom of it
                # we should add additional logging.
                subaccounts.modify(subaccount.pk, group_id=v.instance.pk)
            except AssociatedObjectNotFound:
                logger.error(
                    "Could not update group for new account associated with "
                    "%s (PK = %s) as it could not be found."
                    % (accounts.model_cls.__name__, account.pk), extra={
                        'pk': account.pk,
                        'model_cls': accounts.model_cls.__name__,
                        'subaccounts': str(subaccounts),
                        'group_id': k,
                        'group_accounts': [
                            a.pk for a in v.original.accounts.all()]

                    }
                )

    accounts.clear()
    subaccounts.clear()

    # Duplicate the Fringe instances associated with the Budget.
    fringes = ConcreteObjectSet(model_cls=Fringe, user=user)
    with fringes.transaction():
        for fringe in Fringe.objects.filter(budget=budget):
            fringes.add(fringe, budget=duplicated_budget)

    # Apply the M2M Fringe relationhsips between a given Fringe and it's
    # associated SubAccount(s).
    fringe_through = []
    for k, v in subaccounts.items():
        for fringe in v.original.fringes.all():
            duplicated_fringe = fringes[fringe.pk]
            fringe_through.append(SubAccount.fringes.through(
                fringe_id=duplicated_fringe.new_pk,
                subaccount_id=v.new_pk
            ))
    if fringe_through:
        SubAccount.fringes.through.objects.bulk_create(fringe_through)

    # Duplicate the Markup instances associated with all of the Budget, Account,
    # and SubAccount instances.
    markups = ConcreteObjectSet(model_cls=Markup, user=user)
    with markups.transaction():
        for markup in Markup.objects.filter_by_budget(budget):
            assert markup.content_type_id in (
                source_budget_ct.pk,
                source_a_ct.pk,
                source_sa_ct.pk
            )
            if markup.content_type_id == source_budget_ct.pk:
                markups.add(markup,
                    content_type_id=dest_budget_ct.pk,
                    object_id=duplicated_budget.pk
                )
            elif markup.content_type_id == source_a_ct.pk:
                markups.add(markup,
                    content_type_id=dest_a_ct.pk,
                    object_id=accounts[markup.object_id].new_pk
                )
            else:
                markups.add(markup,
                    content_type_id=dest_sa_ct.pk,
                    object_id=subaccounts[markup.object_id].new_pk
                )

    # Apply the M2M Markup relationships between a given Markup and the
    # associated Account/SubAccount(s).
    account_through = []
    subaccount_through = []
    for k, v in markups.items():
        for account in v.original.accounts.all():
            account_through.append(Account.markups.through(
                account_id=accounts[account.pk].new_pk,
                markup_id=v.new_pk
            ))
        for subaccount in v.original.subaccounts.all():
            subaccount_through.append(SubAccount.markups.through(
                subaccount_id=subaccounts[subaccount.pk].new_pk,
                markup_id=v.new_pk
            ))

    if account_through:
        Account.markups.through.objects.bulk_create(account_through)
    if subaccount_through:
        SubAccount.markups.through.objects.bulk_create(subaccount_through)

    # Duplicate the Actual instances associated with all of the duplicated
    # Markup/SubAccount instances.
    if budget.domain == "budget":
        actuals = ConcreteObjectSet(model_cls=Actual, user=user)
        with actuals.transaction():
            for actual in Actual.objects.filter(budget=budget):
                assert actual.content_type_id in (
                    None, source_sa_ct.pk, markup_ct.pk)
                if actual.content_type_id is None:
                    actuals.add(actual, budget=duplicated_budget)
                elif actual.content_type_id == markup_ct.pk:
                    actuals.add(actual,
                        budget=duplicated_budget,
                        content_type_id=markup_ct.pk,
                        object_id=markups[actual.object_id].new_pk
                    )
                else:
                    actuals.add(actual,
                        budget=duplicated_budget,
                        content_type_id=dest_sa_ct.pk,
                        object_id=subaccounts[actual.object_id].new_pk
                    )

    return duplicated_budget
