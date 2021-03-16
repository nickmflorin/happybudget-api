import collections
import csv
import random

from django.core import management
from django.conf import settings

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


Record = collections.namedtuple('Record',
    ['identifier', 'description', 'type', 'detail'])
RecordGroup = collections.namedtuple('RecordGroup', ['account', 'subaccounts'])


def get_records():
    filepath = settings.BASE_DIR / "management" / "dummy_data_suite" \
        / "mock_budget.csv"
    records = []
    with open(filepath, newline='') as csvfile:
        budget_reader = csv.reader(csvfile, delimiter=',', quotechar='|')
        first_row = False
        for row in budget_reader:
            if first_row is False:
                first_row = True
                continue
            record = Record(
                identifier=row[0],
                description=row[1],
                type=row[2],
                detail=row[3]
            )
            records.append(record)
    return records


def group_records(records):
    grouped = []
    for i, record in enumerate(records):
        if record.identifier.endswith('00'):
            print("Account: %s" % record.identifier)
            group = RecordGroup(account=record, subaccounts=[])
            j = i + 1
            while True:
                if j == len(records):
                    break
                elif records[j].identifier.endswith('00'):
                    break
                print("Sub Account: %s" % records[j].identifier)
                group.subaccounts.append(records[j])
                j += 1
            grouped.append(group)
    return grouped


def establish_budget_from_records(user, records):
    budget = BudgetFactory(user=user)
    for group in records:
        account = Account.objects.create(
            budget=budget,
            created_by=user,
            updated_by=user,
            identifier=group.account.identifier,
            description=group.account.description
        )


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
        records = get_records()
        users = User.objects.filter(is_superuser=True).all()
        establish_mock_budget(users[0], records)

        # for _ in range(num_contacts):
        #     ContactFactory(user=primary_user)

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
