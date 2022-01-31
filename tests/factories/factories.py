import factory

from django.contrib.contenttypes.models import ContentType

from greenbudget.app.account.models import BudgetAccount, TemplateAccount
from greenbudget.app.actual.models import Actual, ActualType
from greenbudget.app.budget.models import Budget
from greenbudget.app.contact.models import Contact
from greenbudget.app.fringe.models import Fringe
from greenbudget.app.group.models import Group
from greenbudget.app.io.models import Attachment
from greenbudget.app.markup.models import Markup
from greenbudget.app.pdf.models import HeaderTemplate
from greenbudget.app.subaccount.models import (
    BudgetSubAccount,
    TemplateSubAccount,
    SubAccountUnit
)
from greenbudget.app.tagging.models import Color
from greenbudget.app.template.models import Template
from greenbudget.app.user.models import User

from .base import CustomModelFactory
from .lazy import Lazy


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


class ColorFactory(CustomModelFactory):
    """
    A DjangoModelFactory to create instances of :obj:`User`.
    """
    code = factory.Faker('color')
    name = factory.Sequence(lambda n: factory.Faker(
        "first_name").generate() + f"{n}")

    class Meta:
        model = Color

    @factory.post_generation
    def content_types(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for content_type in extracted:
                if isinstance(content_type, ContentType):
                    self.content_types.add(content_type)
                else:
                    ct = ContentType.objects.get_for_model(content_type)
                    self.content_types.add(ct)


class TagFactory(CustomModelFactory):
    """
    A DjangoModelFactory to create instances of :obj:`User`.
    """
    order = factory.Sequence(lambda n: n + 1)
    title = factory.Faker('first_name')

    class Meta:
        abstract = True


class UserFactory(CustomModelFactory):
    """
    A DjangoModelFactory to create instances of :obj:`User`.
    """
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    email = factory.Faker('email')
    is_staff = False
    is_admin = False
    is_superuser = False
    is_active = True
    is_first_time = False

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


class BaseBudgetFactory(CustomModelFactory):
    """
    A an abstract DjangoModelFactory to referencing the polymorphic base model
    :obj:`BaseBudget`.
    """
    name = factory.Faker('name')
    created_by = factory.SubFactory(UserFactory)

    class Meta:
        abstract = True


class BudgetFactory(BaseBudgetFactory):
    """
    A DjangoModelFactory to create instances of :obj:`Budget`.
    """
    class Meta:
        model = Budget


class TemplateFactory(BaseBudgetFactory):
    """
    A DjangoModelFactory to create instances of :obj:`Template`.
    """
    class Meta:
        model = Template


class FringeFactory(CustomModelFactory):
    """
    A DjangoModelFactory to create instances of :obj:`Fringe`.
    """
    created_by = factory.SubFactory(UserFactory)
    updated_by = factory.SubFactory(UserFactory)
    name = factory.Faker('name')
    description = factory.Faker('sentence')
    cutoff = None
    rate = 1.00
    unit = Fringe.UNITS.percent

    class Meta:
        model = Fringe


class MarkupFactory(CustomModelFactory):
    """
    A DjangoModelFactory to to create instances of :obj:`Markup`.
    """
    created_by = factory.SubFactory(UserFactory)
    updated_by = factory.SubFactory(UserFactory)
    identifier = factory.Faker('name')
    description = factory.Faker('sentence')

    class Meta:
        model = Markup

    class Params:
        flat = factory.Trait(unit=Markup.UNITS.flat)
        percent = factory.Trait(unit=Markup.UNITS.percent)

    @factory.post_generation
    def accounts(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for child in extracted:
                # pylint: disable=no-member
                self.accounts.add(child)

    @factory.post_generation
    def subaccounts(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for child in extracted:
                # pylint: disable=no-member
                self.subaccounts.add(child)


class GroupFactory(CustomModelFactory):
    """
    A DjangoModelFactory to create instances of :obj:`Group`.
    """
    name = factory.Faker('name')

    class Meta:
        model = Group


class AccountFactory(CustomModelFactory):
    """
    A an abstract DjangoModelFactory to referencing the polymorphic base model
    :obj:`Account`.
    """
    created_by = factory.SubFactory(UserFactory)
    updated_by = factory.SubFactory(UserFactory)
    identifier = factory.Faker('name')
    description = factory.Faker('sentence')

    class Meta:
        abstract = True

    @factory.post_generation
    def markups(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for markup in extracted:
                # pylint: disable=no-member
                self.markups.add(markup)

    @factory.post_generation
    def children(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for child in extracted:
                assert isinstance(child, Lazy), "Child must be lazy!"
                child.create(parent=self)


class BudgetAccountFactory(AccountFactory):
    """
    A DjangoModelFactory to create instances of :obj:`BudgetAccount`.
    """
    class Meta:
        model = BudgetAccount


class TemplateAccountFactory(AccountFactory):
    """
    A DjangoModelFactory to create instances of :obj:`TemplateAccount`.
    """
    class Meta:
        model = TemplateAccount


class SubAccountUnitFactory(
        ConstantTimeMixin('created_at', 'updated_at'), TagFactory):
    """
    A DjangoModelFactory to create instances of :obj:`SubAccountUnit`.
    """
    color = factory.SubFactory(ColorFactory)

    class Meta:
        model = SubAccountUnit


class SubAccountFactory(CustomModelFactory):
    """
    A an abstract DjangoModelFactory to referencing the polymorphic base model
    :obj:`SubAccount`.
    """
    created_by = factory.SubFactory(UserFactory)
    updated_by = factory.SubFactory(UserFactory)
    identifier = factory.Faker('name')
    description = factory.Faker('sentence')

    class Meta:
        abstract = True

    @factory.post_generation
    def children(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for child in extracted:
                assert isinstance(child, Lazy), "Child must be lazy!"
                child.create(parent=self)

    @factory.post_generation
    def markups(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for markup in extracted:
                # pylint: disable=no-member
                self.markups.add(markup)

    @factory.post_generation
    def fringes(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for fringe in extracted:
                # pylint: disable=no-member
                self.fringes.add(fringe)


class BudgetSubAccountFactory(
        ConstantTimeMixin('created_at'), SubAccountFactory):
    """
    A DjangoModelFactory to create instances of :obj:`BudgetSubAccount`.
    """
    parent = factory.SubFactory(BudgetAccountFactory)
    content_type = factory.LazyAttribute(
        lambda o: ContentType.objects.get_for_model(o.parent))
    object_id = factory.SelfAttribute('parent.pk')

    class Meta:
        model = BudgetSubAccount

    @factory.post_generation
    def attachments(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for attachment in extracted:
                self.attachments.add(attachment)


class TemplateSubAccountFactory(
        ConstantTimeMixin('created_at'), SubAccountFactory):
    """
    A DjangoModelFactory to create instances of :obj:`TemplateSubAccount`.
    """
    parent = factory.SubFactory(BudgetAccountFactory)
    content_type = factory.LazyAttribute(
        lambda o: ContentType.objects.get_for_model(o.parent))
    object_id = factory.SelfAttribute('parent.pk')

    class Meta:
        model = TemplateSubAccount


class ActualTypeFactory(
        ConstantTimeMixin('created_at', 'updated_at'), TagFactory):
    """
    A DjangoModelFactory to create instances of :obj:`ActualType`.
    """
    color = factory.SubFactory(ColorFactory)

    class Meta:
        model = ActualType


class ActualFactory(CustomModelFactory):
    """
    A DjangoModelFactory to create instances of :obj:`Actual`.
    """
    created_by = factory.SubFactory(UserFactory)
    updated_by = factory.SubFactory(UserFactory)
    name = factory.Faker('name')
    notes = factory.Faker('sentence')
    purchase_order = "1205023895"
    value = 100.00

    class Meta:
        model = Actual

    @factory.post_generation
    def attachments(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for attachment in extracted:
                self.attachments.add(attachment)


class ContactFactory(CustomModelFactory):
    """
    A DjangoModelFactory to create instances of :obj:`Contact`.
    """
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    email = factory.Faker('email')
    contact_type = Contact.TYPES.vendor
    phone_number = "15555555555"
    rate = 100
    city = "New York"
    company = "GE"
    position = None

    class Meta:
        model = Contact

    @factory.post_generation
    def attachments(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for attachment in extracted:
                self.attachments.add(attachment)


class HeaderTemplateFactory(CustomModelFactory):
    """
    A DjangoModelFactory to create instances of :obj:`HeaderTemplate`.
    """
    name = factory.Faker('name')

    class Meta:
        model = HeaderTemplate


class AttachmentFactory(CustomModelFactory):
    """
    A DjangoModelFactory to create instances of :obj:`Attachment`.
    """
    created_by = factory.SubFactory(UserFactory)

    class Meta:
        model = Attachment
