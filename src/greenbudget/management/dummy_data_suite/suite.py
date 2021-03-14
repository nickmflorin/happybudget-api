from copy import deepcopy
import random

from django.core import management

from greenbudget.app.account.models import Account
from greenbudget.app.actual.models import Actual
from greenbudget.app.budget.models import Budget
from greenbudget.app.comment.models import Comment
from greenbudget.app.subaccount.models import SubAccount
from greenbudget.app.user.models import User

from greenbudget.management.factories import (
    UserFactory, BudgetFactory, AccountFactory, ContactFactory)


num_budgets_per_user = 8
num_users = 20
num_accounts_range = [5, 15]
num_sub_accounts_range = [5, 15]
num_contacts = 30

primary_user_email = "nickmflorin@gmail.com"


def get_random_in_range(rng):
    choices = []
    for _ in range(rng[0], rng[-1] + 1):
        choices.append(_)
    return random.choice(choices)


# def generate_subaccount_random_identifier(starter, budget):


class Selector:
    pass


class ParentSelector(Selector):
    pass


class RandomParentChoice(ParentSelector):
    def select(self, parent):
        return random.choices(parent.instances)


class ModelConfig:
    def __init__(self, klass, factory, references_user=False,
            user_argument="user", count=None, range=None, kwargs=None,
            children=None, pass_through_argument=None,
            exclude_from_delete=None):
        self._klass = klass
        self._factory = factory
        self._references_user = references_user
        self._user_argument = user_argument
        self._children = children
        self._kwargs = kwargs or {}
        self._count = count
        self._range = range
        self._instances = []
        self._pass_through_argument = pass_through_argument
        if self._count is None and self._range is None:
            raise Exception()

    def __call__(self, parent=None, **kwargs):
        count = self._count or get_random_in_range(self._range)
        for _ in range(count):
            for k, v in self._kwargs.items():
                if isinstance(v, Selector):
                    if isinstance(v, ParentSelector) and parent is not None:
                        kwargs[k] = v.select(parent)
                else:
                    kwargs[k] = v
            print("Creating %s Instance (%s/%s)" %
                  (self._klass.__name__, _, count))
            instance = self._factory(**kwargs)
            self._instances.append(instance)

            if self._children is not None:
                for child in self._children:
                    # for instance in self._instances:
                    pass_through_kwargs = {}
                    if self._pass_through_argument is not None:
                        pass_through_kwargs[self._pass_through_argument] = instance  # noqa
                    child(parent=self, **pass_through_kwargs)

    @property
    def instances(self):
        return self._instances


MODELS = [
    ModelConfig(
        klass=User,
        factory=UserFactory,
        count=num_users,
        pass_through_argument="author",
        exclude_from_delete={"email": "nickmflorin@gmail.com"},
        children=[
            ModelConfig(
                klass=Budget,
                factory=BudgetFactory,
                count=num_budgets_per_user,
                pass_through_argument="budget",
                # kwargs={
                #     'author': RandomParentChoice(),
                # },
                children=[
                    ModelConfig(
                        klass=Account,
                        factory=AccountFactory,
                        range=num_accounts_range
                    )
                ]
            )
        ]
    )
]


class DummyDataSuite:
    def generate(self):
        try:
            primary_user = User.objects.get(email=primary_user_email)
        except User.DoesNotExist:
            raise management.CommandError()

        for _ in range(num_contacts):
            ContactFactory(user=primary_user)

        # MODELS[0]()

        # users = []
        # for _ in range(num_users):
        #     user = UserFactory()
        #     users.append(user)

        # budgets = []
        # for user in users:
        #     for _ in range(num_budgets_per_user):
        #         budget = BudgetFactory(author=user)
        #         budgets.append(budget)

        # accounts = []
        # for budget in budgets:
        #     for _ in range(get_random_in_range(num_accounts_range)):
        #         account = AccountFactory(
        #             budget=budget,
        #             created_by=random.choice(users),
        #             updated_by=random.choice(users)
        #         )
        #         accounts.append(account)

        # subaccounts = []
        # for account in accounts:
        #     for _ in range(get_random_in_range(num_sub_accounts_range)):
        #         identifier = 1
        #         if len(subaccounts) != 0:
        #             identifier = subaccounts[-1].identifier
        #         account = SubAccountFactory(
        #             budget=account.budget,
        #             parent=account,
        #             created_by=random.choice(users),
        #             updated_by=random.choice(users),
        #             identifier=identifier
        #         )
        #         accounts.append(account)


suite = DummyDataSuite()
