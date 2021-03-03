import factory
from django.contrib.contenttypes.models import ContentType

from greenbudget.app.account.models import Account
from greenbudget.app.budget.models import Budget
from greenbudget.app.subaccount.models import SubAccount
from greenbudget.app.user.models import User

from .base import CustomModelFactory
from .fields import FutureDateTimeField


def ConstantTimeMixin(*fields):
    """
    If a model has an auto-now time related field, we cannot simply include
    this value in the factory kwargs since it will be overridden to the
    current time when the model is saved.

    If we use this mixin for the factory, then it will allow us to override
    the provided field so it can be explicitly provided in the factory
    arguments without an override from Django on model save.
    """
    class DynamicConstantTimeMixin(object):
        @classmethod
        def post_create(cls, model, **kwargs):
            update_kwargs = {}
            for field in fields:
                if field in kwargs:
                    update_kwargs[field] = kwargs[field]
            instance = super(DynamicConstantTimeMixin, cls).post_create(
                model, **kwargs)
            # Applying a direct update bypasses the auto time fields.
            model.__class__.objects.filter(pk=model.pk).update(**update_kwargs)
            instance.refresh_from_db()
            return instance
    return DynamicConstantTimeMixin


class UserFactory(CustomModelFactory):
    """
    A DjangoModelFactory to create instances of :obj:`User`.
    """
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    email = factory.Faker('email')
    username = factory.SelfAttribute('email')
    is_staff = False
    is_admin = False
    is_superuser = False
    is_active = True

    class Meta:
        model = User

    class Params:
        superuser = factory.Trait(
            is_superuser=True,
            is_admin=False,
            is_staff=True
        )
        admin = factory.Trait(
            is_superuser=False,
            is_admin=True,
            is_staff=False
        )
        staff = factory.Trait(
            is_superuser=False,
            is_admin=False,
            is_staff=True
        )


class BudgetFactory(CustomModelFactory):
    """
    A DjangoModelFactory to create instances of :obj:`Budget`.
    """
    id = factory.Sequence(lambda n: n + 1)
    name = factory.Faker('name')
    author = factory.SubFactory(UserFactory)
    production_type = 1
    shoot_date = FutureDateTimeField()
    delivery_date = FutureDateTimeField()
    build_days = factory.Faker('random_number')
    prelight_days = factory.Faker('random_number')
    studio_shoot_days = factory.Faker('random_number')
    location_days = factory.Faker('random_number')

    class Meta:
        model = Budget


class AccountFactory(CustomModelFactory):
    """
    A DjangoModelFactory to create instances of :obj:`Account`.
    """
    created_by = factory.SubFactory(UserFactory)
    updated_by = factory.SubFactory(UserFactory)
    account_number = factory.Faker('random_number')
    description = factory.Faker('sentence')
    budget = factory.SubFactory(BudgetFactory)

    class Meta:
        model = Account


class SubAccountFactory(CustomModelFactory):
    """
    A DjangoModelFactory to create instances of :obj:`SubAccount`.
    """
    created_by = factory.SubFactory(UserFactory)
    updated_by = factory.SubFactory(UserFactory)
    line = factory.Faker('random_number')
    description = factory.Faker('sentence')
    name = factory.Faker('name')
    unit = SubAccount.UNITS.days
    multiplier = 1.00
    rate = 1.00

    content_object = factory.SubFactory(AccountFactory)
    content_type = factory.LazyAttribute(
        lambda o: ContentType.objects.get_for_model(o.content_object))
    object_id = factory.SelfAttribute('content_object.pk')

    class Meta:
        model = SubAccount
