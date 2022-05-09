from django.db import transaction, models

from happybudget.lib.utils import empty
from happybudget.lib.utils import cumulative_sum

from happybudget.app import model

from happybudget.app.account.models import BudgetAccount
from happybudget.app.budget.models import Budget
from happybudget.app.contact.models import Contact
from happybudget.app.fringe.models import Fringe
from happybudget.app.group.models import Group
from happybudget.app.subaccount.models import BudgetSubAccount, SubAccountUnit
from happybudget.app.tagging.models import Color
from happybudget.app.user.models import User

from .random import (
    select_random, select_random_model_choice, select_random_set)
from . import factories


class ConfigurationError(Exception):
    pass


class ConfigurationParameterError(Exception):
    def __init__(self, config):
        self._config = config


class ConfigurationInvalidError(ConfigurationParameterError):
    def __str__(self):
        return f"The configuration for {self._config.attr} is invalid."


class ConfigurationMissingError(ConfigurationParameterError):
    def __str__(self):
        return f"The configuration for {self._config.attr} is required."


class Configuration:
    def __init__(self, attr, required=False, default=empty):
        self._default = default
        self._attr = attr
        self._required = required

    def raise_missing(self):
        raise ConfigurationMissingError(self)

    def raise_invalid(self):
        raise ConfigurationInvalidError(self)

    def pluck(self, **kwargs):
        if self.required and self.attr not in kwargs:
            self.raise_missing()
        return kwargs.pop(self.attr, self.default)

    @property
    def attr(self):
        return self._attr

    @property
    def default(self):
        return self._default

    @property
    def required(self):
        return self._required


ApplicationDataGeneratorConfigParams = [
    Configuration(attr='num_budgets', required=False, default=1),
    Configuration(attr='num_accounts', required=False, default=10),
    Configuration(attr='num_subaccounts', required=False, default=10),
    Configuration(attr='num_details', required=False, default=10),
    Configuration(attr='include_contacts', required=False, default=True),
    Configuration(attr='num_contacts', required=False, default=0),
    Configuration(attr='include_fringes', required=False, default=True),
    Configuration(attr='num_fringes', required=False, default=10),
    Configuration(attr='num_groups', required=False, default=3),
    Configuration(attr='include_groups', required=False, default=True),
    Configuration(attr='user', required=False, default=None),
    Configuration(attr='pbar', required=False, default=None),
    Configuration(attr='cmd', required=False, default=None),
    Configuration(attr='dry_run', required=False, default=False),
]


def get_user_fields(model_cls):
    return [
        field.name for field in model_cls._meta.get_fields()
        if isinstance(field, models.ForeignKey) and field.related_model is User
    ]


RATES = [float(i) for i in range(20, 1000)]
QUANTITIES = [float(i) for i in range(1, 20)]
MULTIPLIERS = [float(i) for i in range(1, 10)]


class ApplicationDataGeneratorConfig:

    def __init__(self, **config):
        self._progress = 0
        for c in ApplicationDataGeneratorConfigParams:
            setattr(self, f'_{c.attr}', c.pluck(**config))

    @property
    def __dict__(self):
        data = {}
        for c in ApplicationDataGeneratorConfigParams:
            data[c.attr] = getattr(self, f'_{c.attr}')
        return data

    @property
    def pbar(self):
        return self._pbar

    @property
    def user(self):
        if self._user is None:
            raise ConfigurationError(
                "The generator was not configured with a user.")
        return self._user

    @property
    def cmd(self):
        return self._cmd

    @property
    def dry_run(self):
        return self._dry_run

    @property
    def num_budgets(self):
        return self._num_budgets

    @property
    def num_contacts(self):
        if self._include_contacts:
            return self._num_contacts
        return 0

    @property
    def num_groups(self):
        if self._include_groups:
            return self._num_groups
        return 0

    @property
    def num_fringes(self):
        if self._include_fringes:
            return self._num_fringes * self.num_budgets
        return 0

    @property
    def num_accounts(self):
        return self._num_accounts * self.num_budgets

    @property
    def num_subaccounts(self):
        return self._num_subaccounts * self.num_accounts

    @property
    def num_details(self):
        return self.num_subaccounts * self._num_details

    @property
    def num_instances(self):
        return cumulative_sum([
            self.num_budgets,
            self.num_accounts,
            self.num_subaccounts,
            self.num_details,
            self.num_contacts,
            self.num_fringes
        ]) + cumulative_sum([
            self.num_budgets * self.num_groups,
            self.num_accounts * self.num_groups,
            self.num_subaccounts * self.num_groups,
            self.num_details * self.num_groups,
        ])


class ApplicationDataGenerator(ApplicationDataGeneratorConfig):
    def __init__(self, **config):
        explicit_config = config.pop('config', None)
        if explicit_config:
            init_data = explicit_config.__dict__
            init_data.update(**config)
            super().__init__(**init_data)
        else:
            super().__init__(**config)

    def warn(self, msg):
        self.cmd.warn(msg)

    def create(self, model_cls, **kwargs):
        build = kwargs.pop('build', False)
        factory = factories.registry.get(model_cls)

        for user_field in get_user_fields(model_cls):
            if hasattr(model_cls, user_field) and user_field not in kwargs:
                kwargs[user_field] = self.user
        # If running a `dry_run`, only instantiate the instance - do not save
        # it to the database.
        if self.dry_run or build:
            instance = factory.build(**kwargs)
        else:
            instance = factory(**kwargs)
        self.increment_progress()
        return instance

    def increment_progress(self):
        self._progress += 1
        if self.pbar is not None:
            self.pbar.update(self._progress)

    def message(self, data):
        if self.pbar is not None:
            self.pbar.set_description(data)
        elif self.cmd is not None:
            self.cmd.info(data)

    @transaction.atomic
    def __call__(self, pbar=None):
        # Set the user on the model decorator so that we do not get warnings
        # about not being able to infer the user from the model save outside of
        # the request context.
        setattr(model.model.thread, 'user', self.user)

        self.precheck()

        self.group_colors = Color.objects.filter(
            content_types__model='group',
            content_types__app_label='group'
        ).all()

        self.fringe_colors = Color.objects.filter(
            content_types__model='fringe',
            content_types__app_label='fringe'
        ).all()

        self._progress = 0

        if pbar is not None:
            self._pbar = pbar

        contacts = self.create_contacts()
        for bi in range(self._num_budgets):
            self.create_budget(bi, contacts)

    def precheck(self):
        if Color.objects.count() == 0:
            self.warn(
                "No colors found in database. Did you forget to load the "
                "application fixtures?"
            )
        if SubAccountUnit.objects.count() == 0:
            self.warn(
                "No subaccount units found in database. Did you forget to load "
                "the application fixtures?"
            )

    def create_budget(self, i, contacts):
        budget = self.create(Budget, name=f"Budget {i + 1}")
        fringes = self.create_fringes(budget)

        groups = self.create_groups(parent=budget)
        for j in range(self._num_accounts):
            self.create_account(budget, j, fringes, groups, contacts)

    def create_contacts(self):
        contacts = [
            self.create(Contact, build=True)
            for i in range(self.num_contacts)
        ]
        return Contact.objects.bulk_add(contacts)

    def create_groups(self, parent):
        return [self.create(Group,
            name=f"Group {i + 1}",
            color=select_random(self.group_colors, allow_null=True),
            parent=parent
        ) for i in range(self.num_groups)]

    def create_fringes(self, budget):
        return [self.create(Fringe,
            color=select_random(self.fringe_colors, allow_null=True),
            name=f"Fringe {i + 1}",
            budget=budget,
            unit=select_random_model_choice(
                Fringe, 'UNITS', allow_null=True, null_frequency=0.3)
        ) for i in range(self._num_fringes)]

    def create_account(self, budget, i, fringes, groups, contacts):
        account = self.create(BudgetAccount,
            identifier=f"{i}000",
            description=f"{i}000 Description",
            parent=budget,
            group=select_random(groups, null_frequency=0.5, allow_null=True)
        )
        sub_groups = self.create_groups(parent=account)
        for j in range(self._num_subaccounts):
            self.create_subaccount(account, j, fringes, sub_groups, contacts)
        return account

    def _create_subaccount(self, parent, fringes, **kwargs):
        kwargs.setdefault('rate', select_random(
            RATES, null_frequency=0.2, allow_null=True))
        kwargs.setdefault('quantity', select_random(
            QUANTITIES, null_frequency=0.2, allow_null=True))
        kwargs.setdefault('multiplier', select_random(
            MULTIPLIERS, null_frequency=0.6, allow_null=True))

        subaccount = self.create(BudgetSubAccount, parent=parent, **kwargs)
        fringes_for_subaccount = select_random_set(
            fringes, allow_null=False, min_count=0, max_count=4)
        for f in fringes_for_subaccount:
            if self.dry_run:
                self.message(
                    "Ignoring fringe: M2M fields cannot be saved in dry run "
                    "mode"
                )
            else:
                subaccount.fringes.add(f)
        return subaccount

    def create_subaccount(self, account, i, fringes, groups, contacts):
        subaccount = self._create_subaccount(
            parent=account,
            fringes=fringes,
            identifier=f"{account.identifier[:-1]}{i}",
            description=f"{account.identifier[:-1]}{i} Description",
            group=select_random(groups, null_frequency=0.5, allow_null=True),
            contact=select_random(contacts, null_frequency=0.5, allow_null=True)
        )
        detail_groups = self.create_groups(parent=subaccount)
        for j in range(self._num_details):
            self.create_detail(subaccount, j, fringes, detail_groups, contacts)
        return subaccount

    def create_detail(self, subaccount, i, fringes, groups, contacts):
        return self._create_subaccount(
            parent=subaccount,
            fringes=fringes,
            identifier=f"{subaccount.identifier}-{i + 1}",
            description=f"{subaccount.identifier}-{i + 1} Description",
            group=select_random(groups, null_frequency=0.5, allow_null=True),
            contact=select_random(contacts, null_frequency=0.5, allow_null=True)
        )
