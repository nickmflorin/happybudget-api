import collections
import functools
import logging

from django.contrib.contenttypes.models import ContentType
from django.utils.functional import cached_property

from greenbudget.app import signals

from .exceptions import AssociatedObjectNotFound
from .model import PolymorphicObjectSet, ConcreteObjectSet
from .utils import instantiate_duplicate


logger = logging.getLogger('greenbudget')


TimedStat = collections.namedtuple('TimedStat', ['id', 'label'])

TimedStats = [
    TimedStat(id='duplicate_budget', label='Duplicating Budget'),
    TimedStat(id='duplicate_accounts', label='Duplicating Accounts'),
    TimedStat(
        id='instantiating_duplicate_subaccounts',
        label='Instantiating Duplicate SubAccounts'
    ),
    TimedStat(
        id='instantiating_duplicate_subaccounts',
        label='Instantiating Duplicate SubAccounts'
    )
]


class Timer:
    def __init__(self):
        self._stats = {}


def time_with_stat(id):
    def decorator(func):
        @functools.wraps(func)
        def inner(duplicator, *args, **kwargs):
            pass


class Duplicator:
    """
    Manages the duplication of a given :obj:`Budget` or a given :obj:`Template`,
    or the derivation of a new :obj:`Budget` from a given :obj:`Template`.

    The concept of duplication is simply that the entire :obj:`Budget` or
    :obj:`Template` and all of it's related relational data is duplicated
    in an entirely new set of relational instances for the given user.

    The concept of derivation is a little more complex - but in effect
    derivation involves taking a :obj:`Template` (which is effectively a
    template for a :obj:`Budget`) and creates a new :obj:`Budget` from the
    information in the :obj:`Template`.

    Parameters:
    ----------
    budget: :obj:`Budget` or :obj:`Template`
            The :obj:`Budget` or :obj:`Template` that should be duplicated or the
            :obj:`Template` that should be used to derive a new :obj:`Budget`.

    destination_cls: :obj:`type`
        Either Budget or the Template class.

        Default: Type of `budget` parameter

        The determination on whether or not to duplicate or derive is based on
        the following cases:

        (1) `budget` is instance of Budget, `destination_cls` is Budget or None  # noqa
                => Duplicate provided Budget to new Budget
        (2) `budget` is instance of Template, `destination_cls` is Template or None  # noqa
                => Duplicate provided Template to new Template
        (3) `budget` is instance of Template, `destination_cls` is Budget
                => Derive new Budget from provided Template
    """

    def __init__(self, budget, destination_cls=None):
        self._budget = budget
        self._destination_cls = destination_cls or type(budget)

        self._source = None
        self._destination = None

    @property
    def budget(self):
        return self._budget

    @property
    def destination_cls(self):
        return self._destination_cls

    @property
    def source(self):
        return {
            'budget': type(self.budget),
            'account': type(self.budget).account_cls,
            'subaccount': type(self.budget).subaccount_cls
        }

    @property
    def destination(self):
        return {
            'budget': self.destination_cls,
            'account': self.destination_cls.account_cls,
            'subaccount': self.destination_cls.subaccount_cls
        }

    @cached_property
    def source_ct(self):
        return {
            k: ContentType.objects.get_for_model(v)
            for k, v in self.source.items()
        }

    @property
    def source_ct_ids(self):
        return [ct.id for _, ct in self.source_ct.items()]

    @cached_property
    def destination_ct(self):
        return {
            k: ContentType.objects.get_for_model(v)
            for k, v in self.destination.items()
        }

    @signals.disable()
    def __call__(self, user, **overrides):
        """
        Performs the given derivation or duplication of the provided
        :obj:`Budget` or :obj:`Template` for the provided :obj:`User`.

        Parameters:
        ----------
        user: :obj:`User`
            The :obj:`User` that the duplicated :obj:`Budget` or :obj:`Template`
            or the derived :obj:`Budget` should belong to.

        overrides: :obj:`dict`
            Attributes, provided as keyword arguments, that should be set on the
            duplicated or derived :obj:`Budget` or :obj:`Template`, overriding
            any attributes from the original :obj:`Budget` or :obj:`Template`
            instance.
        """
        b = self.duplicate_budget(user, **overrides)
        accounts = self.duplicate_accounts(b, user)
        subaccounts = self.duplicate_subaccounts(accounts, user)
        groups = self.duplicate_groups(b, accounts, subaccounts, user)

        self.associate_groups(groups, accounts, subaccounts)

        # We have to wait until after the Group(s) are associated to persist
        # the Account(s) & SubAccount(s) - and we must do that before we
        # establish the M2M relationships w Fringe(s).
        accounts.clear()
        subaccounts.clear()

        fringes = self.duplicate_fringes(b, user)
        # Associate the duplicated Fringe(s) with the duplicated SubAccount(s).
        self.associate_fringes(fringes, subaccounts)

        markups = self.duplicate_markups(b, accounts, subaccounts, user)
        # Associate the duplicated Markup(s) with the duplicated SubAccount(s)
        # and Account(s).
        self.associate_markups(markups, accounts, subaccounts)

        # Duplicate the Actual instances associated with all of the duplicated
        # Markup/SubAccount instances.  Note that Actual's are not applicable
        # for Templates.
        if self.budget.domain == "budget" and b.domain == 'budget':
            self.duplicate_actuals(b, subaccounts, markups, user)
        return b

    def duplicate_budget(self, user, **overrides):
        # The Budget or Template instance duplicated without any relational data.
        duplicated_budget = instantiate_duplicate(
            instance=self.budget,
            user=user,
            destination_cls=self.destination_cls,
            **overrides
        )
        duplicated_budget.save()
        return duplicated_budget

    def duplicate_accounts(self, duplicated_budget, user):
        # Duplicate the Account instances associated with the Budget or Template.
        accounts = PolymorphicObjectSet(
            model_cls=self.destination_ct["account"].model_class(),
            user=user
        )
        with accounts.transaction():
            for account in self.source_ct["account"].model_class() \
                    .objects.filter(parent=self.budget):
                accounts.add(account, parent=duplicated_budget)
        return accounts

    def duplicate_subaccounts(self, accounts, user):
        # Duplicate the SubAccount instances associated with the Budget or
        # Template. Since a Budget or Template's SubAccount(s) are recursive,
        # and there can be multiple layers of SubAccount(s) at each level, we
        # need to handle each level independently.
        sub_ct = self.destination_ct["subaccount"]
        sub_cls = sub_ct.model_class()

        subaccounts = PolymorphicObjectSet(model_cls=sub_cls, user=user)

        subs_by_level = collections.OrderedDict()
        for sub in self.source_ct["subaccount"].model_class().objects \
                .filter_by_budget(self.budget) \
                .select_related('content_type'):
            subs_by_level.setdefault(
                sub.nested_level,
                PolymorphicObjectSet(model_cls=sub_cls, user=user)
            )
            # Note: We do not add the parents to the SubAccount instances until
            # the parents for each level of the tree can be created before the
            # SubAccount(s) in the next level of the tree are created.
            subs_by_level[sub.nested_level].add(sub)

        # Make sure the the numeric keys of the subaccounts (indexed by level)
        # are consecutive (i.e {0: [...], 1: [...] }).
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
                            content_type_id=self.destination_ct["account"].pk
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
                            content_type_id=sub_ct.pk
                        )
            # Save/clear the leftover or last level of SubAccount(s) in the tree.
            subs_by_level[len(subs_by_level) - 1].clear()

            # Flatten all of the subaccount levels together into one object set.
            subaccounts = PolymorphicObjectSet.from_join(
                list(subs_by_level.values()))
        return subaccounts

    def duplicate_fringes(self, duplicated_budget, user):
        from greenbudget.app.fringe.models import Fringe

        # Duplicate the Fringe instances associated with the Budget.
        fringes = ConcreteObjectSet(model_cls=Fringe, user=user)
        with fringes.transaction():
            for fringe in Fringe.objects.filter(budget=self.budget):
                fringes.add(fringe, budget=duplicated_budget)
        return fringes

    def associate_fringes(self, fringes, subaccounts):
        from greenbudget.app.subaccount.models import SubAccount

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
        return fringe_through

    def duplicate_groups(self, duplicated_budget, accounts, subaccounts, user):
        from greenbudget.app.budget.models import BaseBudget
        from greenbudget.app.account.models import Account
        from greenbudget.app.group.models import Group
        from greenbudget.app.subaccount.models import SubAccount

        # Duplicate the Group instances associated with the Budget, Account and
        # SubAccount instances.
        groups = ConcreteObjectSet(model_cls=Group, user=user)
        with groups.transaction():
            for group in Group.objects.filter_by_budget(self.budget) \
                    .select_related('content_type') \
                    .prefetch_related('accounts', 'subaccounts'):
                model_cls = group.content_type.model_class()
                assert issubclass(model_cls, (BaseBudget, Account, SubAccount))
                if issubclass(model_cls, BaseBudget):
                    groups.add(group,
                        content_type_id=self.destination_ct["budget"].pk,
                        object_id=duplicated_budget.pk
                    )
                elif issubclass(model_cls, Account):
                    groups.add(group,
                        content_type_id=self.destination_ct["account"].pk,
                        object_id=accounts[group.object_id].new_pk
                    )
                else:
                    groups.add(group,
                        content_type_id=self.destination_ct["subaccount"].pk,
                        object_id=subaccounts[group.object_id].new_pk
                    )
        return groups

    def associate_groups(self, groups, accounts, subaccounts):
        # Associate the newly duplicated Group instances with the already
        # duplicated Account/SubAccount instances.
        for k, v in groups.items():
            for account in v.original.accounts.all():
                # This is precautionary, as we have had some bugs related to
                # this.  But if we do not see this for awhile, then we can
                # remove the catch/log.
                try:
                    accounts.modify(account.pk, group_id=v.instance.pk)
                except AssociatedObjectNotFound:
                    logger.error(
                        "Could not update group for new account associated with "
                        "%s (PK = %s) as it could not be found."
                        % (accounts.model_cls.__name__, account.pk), extra={
                            'pk': account.pk,
                            'model_cls': accounts.model_cls.__name__,
                            'group_id': k,
                            'group_accounts': [
                                a.pk for a in v.original.accounts.all()]

                        }
                    )
            for subaccount in v.original.subaccounts.all():
                # This is precautionary, as we have had some bugs related to
                # this. But if we do not see this for awhile, then we can remove
                # the catch/log.
                try:
                    subaccounts.modify(subaccount.pk, group_id=v.instance.pk)
                except AssociatedObjectNotFound:
                    logger.error(
                        "Could not update group for new account associated with "
                        "%s (PK = %s) as it could not be found."
                        % (accounts.model_cls.__name__, account.pk), extra={
                            'pk': account.pk,
                            'model_cls': accounts.model_cls.__name__,
                            'group_id': k,
                            'group_accounts': [
                                a.pk for a in v.original.accounts.all()]

                        }
                    )

    def duplicate_markups(self, duplicated_budget, accounts, subaccounts, user):
        from greenbudget.app.markup.models import Markup

        markups = ConcreteObjectSet(model_cls=Markup, user=user)
        with markups.transaction():
            for markup in Markup.objects.filter_by_budget(self.budget):
                assert markup.content_type_id in self.source_ct_ids
                if markup.content_type_id == self.source_ct['budget'].pk:
                    markups.add(markup,
                        content_type_id=self.destination_ct['budget'].pk,
                        object_id=duplicated_budget.pk
                    )
                elif markup.content_type_id == self.source_ct['account'].pk:
                    markups.add(markup,
                        content_type_id=self.destination_ct['account'].pk,
                        object_id=accounts[markup.object_id].new_pk
                    )
                else:
                    markups.add(markup,
                        content_type_id=self.destination_ct['subaccount'].pk,
                        object_id=subaccounts[markup.object_id].new_pk
                    )
        return markups

    def associate_markups(self, markups, accounts, subaccounts):
        from greenbudget.app.account.models import Account
        from greenbudget.app.subaccount.models import SubAccount

        # Apply the M2M Markup relationships between a given Markup and the
        # associated Account/SubAccount(s).
        account_through = []
        subaccount_through = []
        for k, v in markups.items():
            for account in v.original.accounts.all():
                # This is precautionary, as we have had some bugs related to
                # this.  But if we do not see this for awhile, then we can
                # remove the catch/log.
                try:
                    duplicated_account = accounts[account.pk]
                except AssociatedObjectNotFound:
                    logger.error(
                        "Could not assign account to new markup as its original "
                        "could not be found.", extra={
                            'original_account_pk': account.pk,
                            'original_markup_pk': v.original.pk,
                            'duplicated_markup_pk': v.new_pk,
                            'original_model_cls': account.__class__.__name__,
                            'duplicated_model_cls': accounts.model_cls.__name__,
                        }
                    )
                else:
                    account_through.append(Account.markups.through(
                        account_id=duplicated_account.new_pk,
                        markup_id=v.new_pk
                    ))
            for subaccount in v.original.subaccounts.all():
                # This is precautionary, as we have had some bugs related to
                # this.  But if we do not see this for awhile, then we can
                # remove the catch/log.
                try:
                    duplicated_subaccount = subaccounts[subaccount.pk]
                except AssociatedObjectNotFound:
                    logger.error(
                        "Could not assign subaccount to new markup as its "
                        "original could not be found.", extra={
                            'original_subaccount_pk': subaccount.pk,
                            'original_markup_pk': v.original.pk,
                            'duplicated_markup_pk': v.new_pk,
                            'original_model_cls': subaccount.__class__.__name__,
                            'duplicated_model_cls': (
                                subaccounts.model_cls.__name__)
                        }
                    )
                else:
                    subaccount_through.append(SubAccount.markups.through(
                        subaccount_id=duplicated_subaccount.new_pk,
                        markup_id=v.new_pk
                    ))

        if account_through:
            Account.markups.through.objects.bulk_create(account_through)
        if subaccount_through:
            SubAccount.markups.through.objects.bulk_create(subaccount_through)

    def duplicate_actuals(self, duplicated_budget, subaccounts, markups, user):
        from greenbudget.app.actual.models import Actual
        from greenbudget.app.markup.models import Markup

        markup_ct = ContentType.objects.get_for_model(Markup)

        actuals = ConcreteObjectSet(model_cls=Actual, user=user)
        with actuals.transaction():
            for actual in Actual.objects.filter(budget=self.budget):
                assert actual.content_type_id in (
                    None, self.source_ct['subaccount'].pk, markup_ct.pk)
                kwargs = {'budget': duplicated_budget}
                # When creating the duplicated Actual, make sure that the
                # actual-owner relationship is maintained (if it exists).
                if actual.content_type_id is not None \
                        and actual.content_type_id == markup_ct.pk:
                    # Here, the Actual is tied to a Markup, so we need to
                    # make sure that relationship is established by associating
                    # the duplciated Actual to the original Markup's duplicated
                    # form.
                    kwargs.update(
                        content_type_id=markup_ct.pk,
                        object_id=markups[actual.object_id].new_pk
                    )
                elif actual.content_type_id is not None:
                    # Here, the Actual is tied to a SubAccount, so we need to
                    # make sure that relationship is established by associating
                    # the duplciated Actual to the original SubAccount's
                    # duplicated form.
                    kwargs.update(
                        content_type_id=self.destination_ct['subaccount'].pk,
                        object_id=subaccounts[actual.object_id].new_pk
                    )
                actuals.add(actual, **kwargs)
        return actuals
