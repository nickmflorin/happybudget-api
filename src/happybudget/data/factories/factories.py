import factory

from django.contrib.contenttypes.models import ContentType

from happybudget.app.account.models import BudgetAccount, TemplateAccount
from happybudget.app.actual.models import Actual, ActualType
from happybudget.app.authentication.models import PublicToken
from happybudget.app.budget.models import Budget
from happybudget.app.collaborator.models import Collaborator
from happybudget.app.contact.models import Contact
from happybudget.app.fringe.models import Fringe
from happybudget.app.group.models import Group
from happybudget.app.io.models import Attachment
from happybudget.app.markup.models import Markup
from happybudget.app.pdf.models import HeaderTemplate
from happybudget.app.subaccount.models import (
    BudgetSubAccount,
    TemplateSubAccount,
    SubAccountUnit
)
from happybudget.app.tagging.models import Color
from happybudget.app.template.models import Template
from happybudget.app.user.models import User

from .base import CustomModelFactory


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

    class Meta:
        abstract = True


class PublicTokenFactory(CustomModelFactory):
    """
    A DjangoModelFactory to create instances of :obj:`PublicToken`.
    """
    class Meta:
        model = PublicToken


class UserFactory(CustomModelFactory):
    """
    A DjangoModelFactory to create instances of :obj:`User`.
    """
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    email = factory.Faker('email')
    is_staff = False
    is_superuser = False
    is_active = True
    is_first_time = False
    is_verified = True
    password = "test_password"

    class Meta:
        model = User

    class Params:
        superuser = factory.Trait(is_superuser=True, is_staff=True)
        staff = factory.Trait(is_superuser=False, is_staff=True)


class BaseBudgetFactory(CustomModelFactory):
    """
    A an abstract DjangoModelFactory to referencing the polymorphic base model
    :obj:`BaseBudget`.
    """
    name = factory.Sequence(lambda n: f"Budget {n}")
    created_by = factory.SubFactory(UserFactory)
    updated_by = factory.SubFactory(UserFactory)

    class Meta:
        abstract = True


class CollaboratorFactory(CustomModelFactory):
    """
    A DjangoModelFactory to create instances of :obj:`Collaborator`.
    """
    content_type = factory.LazyAttribute(
        lambda o: ContentType.objects.get_for_model(o.instance))
    object_id = factory.SelfAttribute('instance.pk')
    user = factory.SubFactory(UserFactory)

    class Meta:
        model = Collaborator

    class Params:
        view_only = factory.Trait(
            access_type=Collaborator.ACCESS_TYPES.view_only)
        owner = factory.Trait(access_type=Collaborator.ACCESS_TYPES.owner)
        editor = factory.Trait(access_type=Collaborator.ACCESS_TYPES.editor)


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

    name = factory.Sequence(lambda n: f"Fringe {n}")
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
    identifier = factory.Sequence(lambda n: f"100{n}")
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


class SubAccountUnitFactory(TagFactory):
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
    identifier = factory.Sequence(lambda n: f"1000-{n}")
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
    def fringes(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for fringe in extracted:
                # pylint: disable=no-member
                self.fringes.add(fringe)


class BudgetSubAccountFactory(SubAccountFactory):
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


class TemplateSubAccountFactory(SubAccountFactory):
    """
    A DjangoModelFactory to create instances of :obj:`TemplateSubAccount`.
    """
    parent = factory.SubFactory(BudgetAccountFactory)
    content_type = factory.LazyAttribute(
        lambda o: ContentType.objects.get_for_model(o.parent))
    object_id = factory.SelfAttribute('parent.pk')

    class Meta:
        model = TemplateSubAccount


class ActualTypeFactory(TagFactory):
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
    created_by = factory.SubFactory(UserFactory)
    updated_by = factory.SubFactory(UserFactory)
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    email = factory.Faker('email')
    contact_type = Contact.TYPES.vendor
    phone_number = "15555555555"
    rate = 100
    city = factory.Faker('city')
    company = factory.Faker('company')
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
