import random

from django.contrib.contenttypes.models import ContentType
from django.db import transaction

from greenbudget.lib.utils import empty
from greenbudget.lib.utils import cumulative_sum

from greenbudget.app.account.models import BudgetAccount
from greenbudget.app.budget.models import Budget
from greenbudget.app.fringe.models import Fringe
from greenbudget.app.tagging.models import Color
from greenbudget.app.subaccount.models import BudgetSubAccount, SubAccountUnit

from . import factories


class ConfigurationError(Exception):
    def __init__(self, config):
        self._config = config


class ConfigurationInvalidError(ConfigurationError):
    def __str__(self):
        return f"The configuration for {self._config.attr} is invalid."


class ConfigurationMissingError(ConfigurationError):
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


ApplicationDataGeneratorConfig = [
    Configuration(attr='num_budgets', required=False, default=1),
    Configuration(attr='num_accounts', required=False, default=10),
    Configuration(attr='num_subaccounts', required=False, default=10),
    Configuration(attr='num_details', required=False, default=10),
    Configuration(attr='num_contacts', required=False, default=0),
    Configuration(attr='num_fringes', required=False, default=10)
]


USER_FIELDS = ['created_by', 'updated_by']


def select_random_index(data, **kwargs):
    allow_null = kwargs.pop('allow_null', False)
    if len(data) == 0:
        if not allow_null:
            raise Exception("Cannot select value from empty sequence.")
        return None

    null_frequency = kwargs.pop('null_frequency', 0.0)
    if allow_null is False and null_frequency != 0.0:
        raise Exception(
            "Cannot provide null frequency if null values not allowed.")

    assert null_frequency <= 1.0 and null_frequency >= 0.0, \
        "The null frequency must be between 0 and 1."

    if null_frequency != 0.0:
        uniform = random.randint(0, 100)
        if uniform >= null_frequency <= null_frequency * 100.0:
            return None
    return random.choice([i for i in range(len(data))])


def select_random(data, **kwargs):
    index = select_random_index(data, **kwargs)
    if index is None:
        return None
    return data[index]


def select_random_count(data, **kwargs):
    min_count = kwargs.pop('min_count', 0)
    max_count = min(kwargs.pop('max_count', len(data)), len(data))

    assert min_count <= max_count, \
        "The min count must be smaller than or equal to the max count."

    count = kwargs.pop('count', None)
    if count is not None:
        return count
    elif min_count == max_count:
        return min_count
    return random.choice(
        [i for i in range(max_count - min_count + 1)]) + min_count


def select_random_set(data, **kwargs):
    total_count = select_random_count(data, **kwargs)

    # We have to be careful with empty datasets, as an empty data set may return
    # a None value which can cause an infinite loop here if we do not return
    # when this is detected.
    current_count = 0
    current_selection = []
    while current_count < total_count:
        choice = select_random(data, **kwargs)
        if choice is None and len(data) == 0:
            return [None]
        elif choice not in current_selection:
            current_selection.append(choice)
            current_count += 1
    return current_selection


def select_random_model_choice(model_cls, attr, **kwargs):
    choices = getattr(model_cls, attr)
    choice = select_random(choices._doubles, **kwargs)
    if choice is not None:
        return choice[0]
    return None


class ApplicationDataGenerator:
    def __init__(self, user, **config):
        self._user = user
        self._progress_bar = None
        self._progress = 0
        self._on_warning = config.pop('on_warning', None)
        for c in ApplicationDataGeneratorConfig:
            setattr(self, f'_{c.attr}', c.pluck(**config))

    @property
    def num_budgets(self):
        return self._num_budgets

    @property
    def num_contacts(self):
        return self._num_contacts

    @property
    def num_fringes(self):
        return self._num_fringes * self.num_budgets

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
        ])

    def warn(self, msg):
        if self._on_warning is not None:
            self._on_warning(msg)
        else:
            print(msg)

    def create(self, model_cls, **kwargs):
        factory = factories.registry.get(model_cls)
        for user_field in USER_FIELDS:
            if hasattr(model_cls, user_field) and user_field not in kwargs:
                kwargs[user_field] = self._user
        instance = factory(**kwargs)
        self.increment_progress()
        return instance

    def increment_progress(self):
        self._progress += 1
        self._progress_bar.update(self._progress)

    @transaction.atomic
    def __call__(self, progress_bar=None):
        self.precheck()
        self._progress = 0
        self._progress_bar = progress_bar
        for bi in range(self._num_budgets):
            self.create_budget(bi)

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

    def create_budget(self, i):
        budget = self.create(Budget, name=f"Budget {i + 1}")
        fringes = self.create_fringes(budget)
        for j in range(self._num_accounts):
            self.create_account(budget, j, fringes)

    def create_fringes(self, budget):
        colors = Color.objects.filter(
            content_types__model='fringe',
            content_types__app_label='fringe'
        ).all()
        return [self.create(Fringe,
            color=select_random(colors, allow_null=True),
            name=f"Fringe {i + 1}",
            budget=budget,
            unit=select_random_model_choice(
                Fringe, 'UNITS', allow_null=True, null_frequency=0.3)
        ) for i in range(self._num_fringes)]

    def create_account(self, budget, i, fringes):
        account = self.create(BudgetAccount,
            identifier=f"{i}000",
            description=f"{i}000 Description",
            parent=budget
        )
        for j in range(self._num_subaccounts):
            self.create_subaccount(account, j, fringes)

    def _create_subaccount(self, parent, fringes, **kwargs):
        subaccount = self.create(BudgetSubAccount,
            object_id=parent.pk,
            content_type_id=ContentType.objects.get_for_model(type(parent)).id,
            **kwargs
        )
        fringes_for_subaccount = select_random_set(
            fringes, allow_null=False, min_count=0, max_count=4)
        for f in fringes_for_subaccount:
            subaccount.fringes.add(f)
        return subaccount

    def create_subaccount(self, account, i, fringes):
        subaccount = self._create_subaccount(
            parent=account,
            fringes=fringes,
            identifier=f"{account.description[:-1]}{i}",
            description=f"{account.description[:-1]}{i} Description",
        )
        for j in range(self._num_details):
            self.create_detail(subaccount, j)

    def create_detail(self, subaccount, i, fringes):
        return self._create_subaccount(
            parent=subaccount,
            fringes=fringes,
            identifier=f"{subaccount.description}-{i + 1}",
            description=f"{subaccount.description}-{i + 1} Description",
        )