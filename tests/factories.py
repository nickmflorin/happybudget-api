# pylint: disable=redefined-outer-name
import copy
import functools
from io import BytesIO
from PIL import Image

from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.contenttypes.models import ContentType

import pytest

from happybudget.data import factories
from happybudget.app.budget.models import Budget
from happybudget.app.template.models import Template


@pytest.fixture
def default_owner(user):
    """
    Determines what :obj:`User` should be used for defining the instance's
    ownership in the case that it is not explicitly provided to the factory.

    The ForeignKey field that dictates the :obj:`User` that owns a given model
    instance will always be a required field.  For means of convenience, we
    allow the field to be omitted in tests with the understanding that it will
    default to the most common use cases.

    If the value for the ForeignKey field that dictates the :obj:`User` that
    owns a given model is not defined when creating the instance via the
    factory, we will attempt one of the following two things:

    (1) Use the same :obj:`User` that is defined as the owner of a model that
        is related to the one we are creating.

        For example, if we are creating a :obj:`BudgetAccount` and do not define
        the `created_by` field, the field will default to the value of the
        `created_by` field for the :obj:`Budget` that the :obj:`BudgetAccount`
        is being created for.

    (2) If (1) cannot be accomplished, we will simply set the instance's owning
        :obj:`User` based on the common `user` fixture model.

        Note that this is an edge case, as the ForeignKey field that dictates
        the :obj:`User` will always be required - so we would hit an error
        creating the instance anyways.

        For example, if we are creating a :obj:`BudgetAccount` and do not define
        the :obj:`Budget` that the :obj:`BudgetAccount` is being created for,
        the instance will not successfully be created since the :obj:`Budget`
        that the :obj:`BudgetAccount` relates to is always required.
    """
    def inner(related_attr, ownership_field, **kwargs):
        if related_attr in kwargs \
                and hasattr(kwargs[related_attr], ownership_field) \
                and getattr(kwargs[related_attr], ownership_field) is not None:
            return getattr(kwargs[related_attr], ownership_field)
        return user
    return inner


def domain_fixture(**contextuals):
    """
    Decorates a fixture such that the fixture uses the factory associated
    with the domain provided to the fixture method.

    Usage:
    -----
    >>> @domain_fixture(budget=FactoryA, template=FactoryB)
    >>> def my_fixture():
    >>>     pass

    When using the fixture `my_fixture` in tests, the factory that will be
    used will depend on whether or not the fixture function is called with
    a domain value equal to `budget` or `template`.
    """
    related_attr = contextuals.pop('related_attr', None)
    ownership_field = contextuals.pop('ownership_field', 'created_by')

    def decorator(func):
        @pytest.fixture
        def fixture(default_owner, user):
            @allow_multiple
            def inner(*args, **kw):
                domain = kw.pop('domain', 'budget')
                assert domain in ('budget', 'template'), \
                    "Invalid domain %s." % domain
                factory = contextuals[domain]
                if hasattr(factory._meta.model, 'created_by'):
                    if related_attr is not None:
                        kw.setdefault(
                            ownership_field,
                            default_owner(related_attr, ownership_field, **kw)
                        )
                    else:
                        kw.setdefault(ownership_field, user)
                if hasattr(factory._meta.model, 'updated_by'):
                    kw.setdefault('updated_by', kw.get(ownership_field, user))
                return factory(*args, **kw)
            inner.__name__ = func.__name__
            return inner

        fixture.__name__ = func.__name__
        return fixture

    return decorator


def allow_multiple(func):
    """
    Allows a factory fixture to create multiple instances with the same
    keyword arguments if a `count` parameter is provided.  The keyword
    arguments that the factory fixture is called with will be applied to all
    instances that are created, unless the keyword parameter ends with `_array`.

    In the case that the keyword parameter ends with `_array`, the parameter
    value must be an iterable with length equal to `count`, and each of the
    values of the array will be used sequantially when creating the instances.

    Usage:
    -----
    >>> @allow_multiple
    >>> def factory_fn(**kwargs):
    >>>    return create_budget(**kwargs)

    When the decorator is used in the above case, we can call the factory
    function as `create_budget(count=3, name='Budget')`.  This will create 3
    :obj:`Budget` instances, all with the same name; "Budget".  If we call
    the factory function as `create_budget(count=3, name=["a", "b", "c"])`,
    then 3 :obj:`Budget` instances will be created, with names "a", "b" and
    "c" respectively.
    """
    @functools.wraps(func)
    def inner(*args, **kwargs):
        count = kwargs.pop('count', None)
        if count is not None:
            raw_array_properties = {}
            for k, v in kwargs.items():
                if k.endswith('_array'):
                    if not isinstance(v, (tuple, list)):
                        raise Exception(
                            f"Model factory attribute {k} was specified but "
                            "the value was not an iterable!"
                        )
                    elif len(v) != count:
                        raise Exception(
                            f"Model factory attribute {k} was specified but "
                            "the value did not have a length equal to the "
                            "count parameter!"
                        )
                    raw_array_properties[k] = v

            array_properties = {}
            for k, v in raw_array_properties.items():
                array_properties[k.split('_array')[0]] = kwargs.pop(k)

            instances = []
            for i in range(count):
                model_kwargs = copy.deepcopy(kwargs)
                for k, v in array_properties.items():
                    model_kwargs[k] = v[i]
                instances.append(func(*args, **model_kwargs))
            return instances
        return func(*args, **kwargs)
    return inner


@pytest.fixture
def create_attachment(db, user, temp_media_root):
    """
    A fixture that creates a :obj:`Attachment` instance using the
    :obj:`AttachmentFactory`.  Any data that is not explicitly provided will
    be randomly generated by the factory.

    Usage:
    -----
    >>> def test_attachment(create_attachment, user):
    >>>     attachment = create_attachment()
    >>>     assert attachment.created_by == user
    """
    @allow_multiple
    def inner(*args, **kwargs):
        kwargs.setdefault('created_by', user)
        if 'file' not in kwargs:
            name = kwargs.pop('name', 'test')
            if '.' in name:
                ext = name.split('.')[1]
                name = name.split('.')[0]
            else:
                ext = kwargs.pop('ext', 'jpeg')
            image = BytesIO()
            Image.new('RGB', (100, 100)).save(image, ext)
            image.seek(0)
            kwargs['file'] = SimpleUploadedFile(
                '%s.%s' % (name, ext), image.getvalue())
        return factories.AttachmentFactory(*args, **kwargs)

    inner.__name__ = 'create_attachment'
    return inner


@pytest.fixture
def create_color(db):
    """
    A fixture that creates a :obj:`Color` instance using the
    :obj:`ColorFactory`.  Any data that is not explicitly provided will
    be randomly generated by the factory.

    Usage:
    -----
    >>> def test_color(create_color):
    >>>     color = create_color()
    >>>     color.code
    >>>     #EFEFEF
    """
    @allow_multiple
    def inner(*args, **kwargs):
        return factories.ColorFactory(*args, **kwargs)

    inner.__name__ = 'create_color'
    return inner


@pytest.fixture
def create_user(db):
    """
    A fixture that creates a :obj:`User` instance using the
    :obj:`UserFactory`.  Any data that is not explicitly provided will
    be randomly generated by the factory.

    Usage:
    -----
    >>> def test_user(create_user):
    >>>     user = create_user(first_name="jack")
    >>>     assert user.first_name == "jack"
    """
    @allow_multiple
    def inner(*args, **kwargs):
        return factories.UserFactory(*args, **kwargs)

    inner.__name__ = 'create_user'
    return inner


@pytest.fixture
def create_public_token(user):
    """
    A fixture that creates a :obj:`PublicToken` instance using the
    :obj:`PublicTokenFactory`.  Any data that is not explicitly provided will
    be randomly generated by the factory.

    Usage:
    -----
    >>> def test_public_token(create_public_token):
    >>>     token = create_public_token(instance=budget)
    >>>     assert token.instance == budget
    """
    def inner(*args, **kwargs):
        kwargs.setdefault('created_by', user)
        if 'instance' in kwargs:
            instance = kwargs.pop('instance')
            ct = ContentType.objects.get_for_model(type(instance))
            kwargs.update(content_type=ct, object_id=instance.pk)
        return factories.PublicTokenFactory(*args, **kwargs)

    inner.__name__ = 'create_public_token'
    return inner


@pytest.fixture
def create_collaborator(db):
    """
    A fixture that creates a :obj:`Collaborator` instance using the
    :obj:`CollaboratorFactory`.  Any data that is not explicitly provided will
    be randomly generated by the factory.

    Usage:
    -----
    >>> def test_collaborator(create_collaborator, create_budget, user):
    >>>     budget = create_budget(name='Test Budget')
    >>>     collaborator = create_collaborator(instance=budget, user=user)
    >>>     assert collaborator.instance.name == 'Test Budget'
    """
    @allow_multiple
    def inner(*args, **kwargs):
        return factories.CollaboratorFactory(*args, **kwargs)

    inner.__name__ = 'create_collaborator'
    return inner


@pytest.fixture
def create_template(user):
    """
    A fixture that creates a :obj:`Template` instance using the
    :obj:`TemplateFactory`.  Any data that is not explicitly provided will
    be randomly generated by the factory.

    Usage:
    -----
    >>> def test_template(create_template):
    >>>     template = create_template(name='Test Template')
    >>>     assert template.name == 'Test Template'
    """
    @allow_multiple
    def inner(*args, **kwargs):
        kwargs.setdefault('created_by', user)
        kwargs.setdefault('updated_by', kwargs['created_by'])
        return factories.TemplateFactory(*args, **kwargs)

    inner.__name__ = 'create_template'
    return inner


@domain_fixture(
    budget=factories.BudgetFactory,
    template=factories.TemplateFactory
)
def create_budget():
    """
    A fixture that creates either a :obj:`Budget` or :obj:`Template` instance,
    depending on the `domain` argument supplied, using associated factories.

    The default domain is `budget`.

    Usage:
    -----
    >>> def test_budget(create_budget):
    >>>     budget = create_budget(domain='budget')
    >>>     assert isinstance(budget, Budget)
    """


@pytest.fixture
def create_fringe(default_owner):
    """
    A fixture that creates a :obj:`Fringe` instance using the
    :obj:`FringeFactory`.  Any data that is not explicitly provided will
    be randomly generated by the factory.

    Usage:
    -----
    >>> def test_fringe(create_fringe):
    >>>     fringe = create_fringe(rate=2.5)
    >>>     assert fringe.rate == 2.5
    """
    @allow_multiple
    def inner(*args, **kwargs):
        kwargs.setdefault(
            'created_by', default_owner('budget', 'created_by', **kwargs))
        kwargs.setdefault('updated_by', kwargs['created_by'])
        return factories.FringeFactory(*args, **kwargs)
    inner.__name__ = 'create_fringe'
    return inner


@pytest.fixture
def create_budget_account(default_owner):
    """
    A fixture that creates a :obj:`BudgetAccount` instance using the
    :obj:`BudgetAccountFactory`.  Any data that is not explicitly provided will
    be randomly generated by the factory.

    Usage:
    -----
    >>> def test_budget_account(create_budget_account):
    >>>     account = create_budget_account(description='Test Account')
    >>>     assert account.description == 'Test Account'
    """
    @allow_multiple
    def inner(*args, **kwargs):
        kwargs.setdefault(
            'created_by', default_owner('parent', 'created_by', **kwargs))
        kwargs.setdefault('updated_by', kwargs['created_by'])
        return factories.BudgetAccountFactory(*args, **kwargs)
    inner.__name__ = 'create_budget_account'
    return inner


@pytest.fixture
def create_template_account(default_owner):
    """
    A fixture that creates a :obj:`TemplateAccount` instance using the
    :obj:`TemplateAccountFactory`.  Any data that is not explicitly provided
    will be randomly generated by the factory.

    Usage:
    -----
    >>> def test_temlpate_account(create_template_account):
    >>>     account = create_template_account(description='Test Account')
    >>>     assert account.description == 'Test Account'
    """
    @allow_multiple
    def inner(*args, **kwargs):
        kwargs.setdefault(
            'created_by', default_owner('parent', 'created_by', **kwargs))
        kwargs.setdefault('updated_by', kwargs['created_by'])
        return factories.TemplateAccountFactory(*args, **kwargs)
    inner.__name__ = 'create_template_account'
    return inner


@domain_fixture(
    budget=factories.BudgetAccountFactory,
    template=factories.TemplateAccountFactory,
    related_attr='parent'
)
def create_account():
    """
    A fixture that creates either a :obj:`BudgetAccount` or
    :obj:`TemplateAccount` instance, depending on the `domain` argument supplied,
    using associated factories.

    The default domain is `budget`.

    Usage:
    -----
    >>> def test_account(create_account):
    >>>     subaccount = create_account(domain='budget')
    >>>     assert isinstance(subaccount, BudgetAccount)
    """


@pytest.fixture
def create_subaccount_unit(db):
    """
    A fixture that creates a :obj:`SubAccountUnit` instance using the
    :obj:`SubAccountUnitFactory`.  Any data that is not explicitly provided
    will be randomly generated by the factory.

    Usage:
    -----
    >>> def test_subaccount_unit(create_subaccount_unit):
    >>>     unit = create_subaccount_unit(title='Test')
    >>>     assert unit.title == 'Test'
    """
    @allow_multiple
    def inner(*args, **kwargs):
        return factories.SubAccountUnitFactory(*args, **kwargs)
    inner.__name__ = 'create_subaccount_unit'
    return inner


@pytest.fixture
def create_budget_subaccount(default_owner):
    """
    A fixture that creates a :obj:`BudgetSubAccount` instance using the
    :obj:`BudgetSubAccountFactory`.  Any data that is not explicitly provided
    will be randomly generated by the factory.

    Usage:
    -----
    >>> def test_budget_subaccount(create_budget_subaccount):
    >>>     subaccount = create_budget_subaccount(name='Test Account')
    >>>     assert subaccount.name == 'Test Account'
    """
    @allow_multiple
    def inner(*args, **kwargs):
        kwargs.setdefault(
            'created_by', default_owner('parent', 'created_by', **kwargs))
        kwargs.setdefault('updated_by', kwargs['created_by'])
        return factories.BudgetSubAccountFactory(*args, **kwargs)
    inner.__name__ = 'create_budget_subaccount'
    return inner


@pytest.fixture
def create_template_subaccount(default_owner):
    """
    A fixture that creates a :obj:`TemplateSubAccount` instance using the
    :obj:`TemplateSubAccountFactory`.  Any data that is not explicitly provided
    will be randomly generated by the factory.

    Usage:
    -----
    >>> def test_template_subaccount(create_template_subaccount):
    >>>     subaccount = create_template_subaccount(name='Test Account')
    >>>     assert subaccount.name == 'Test Account'
    """
    @allow_multiple
    def inner(*args, **kwargs):
        kwargs.setdefault(
            'created_by', default_owner('parent', 'created_by', **kwargs))
        kwargs.setdefault('updated_by', kwargs['created_by'])
        return factories.TemplateSubAccountFactory(*args, **kwargs)
    inner.__name__ = 'create_template_subaccount'
    return inner


@domain_fixture(
    budget=factories.BudgetSubAccountFactory,
    template=factories.TemplateSubAccountFactory,
    related_attr='parent'
)
def create_subaccount():
    """
    A fixture that creates either a :obj:`BudgetSubAccount` or
    :obj:`TemplateSubAccount` instance, depending on the `domain` argument
    supplied, using associated factories.

    The default domain is `budget`.

    Usage:
    -----
    >>> def test_subaccount(create_subaccount):
    >>>     subaccount = create_subaccount(domain='budget')
    >>>     assert isinstance(subaccount, BudgetSubAccount)
    """


@pytest.fixture
def create_group(default_owner):
    """
    A fixture that creates a :obj:`Group` instance using the
    :obj:`GroupFactory`.  Any data that is not explicitly provided will be
    randomly generated by the factory.

    Usage:
    -----
    >>> def test_group(create_group):
    >>>     group = create_group(name='Test Group')
    >>>     assert group.name == 'Test Group'
    """
    @allow_multiple
    def inner(*args, **kwargs):
        kwargs.setdefault(
            'created_by', default_owner('parent', 'created_by', **kwargs))
        kwargs.setdefault('updated_by', kwargs['created_by'])
        if 'parent' in kwargs:
            parent = kwargs.pop('parent')
            ct = ContentType.objects.get_for_model(type(parent))
            kwargs.update(content_type=ct, object_id=parent.pk)
        return factories.GroupFactory(*args, **kwargs)
    inner.__name__ = 'create_group'
    return inner


@pytest.fixture
def create_markup(default_owner):
    """
    A fixture that creates a :obj:`Markup` instance using the
    :obj:`MarkupFactory`.  Any data that is not explicitly provided will be
    randomly generated by the factory.

    Usage:
    -----
    >>> def test_markup(create_markup):
    >>>     markup = create_markup(identifier='Test Markup')
    >>>     assert markup.identifier == 'Test Markup'
    """
    @allow_multiple
    def inner(*args, **kwargs):
        kwargs.setdefault(
            'created_by', default_owner('owner', 'created_by', **kwargs))
        kwargs.setdefault('updated_by', kwargs['created_by'])
        return factories.MarkupFactory(*args, **kwargs)
    inner.__name__ = 'create_markup'
    return inner


@pytest.fixture
def create_actual_type(db):
    """
    A fixture that creates a :obj:`ActualType` instance using the
    :obj:`ActualTypeFactory`.  Any data that is not explicitly provided
    will be randomly generated by the factory.

    Usage:
    -----
    >>> def test_actual_type(create_actual_type):
    >>>     type = create_actual_type(title='Test')
    >>>     assert type.title == 'Test'
    """
    @allow_multiple
    def inner(*args, **kwargs):
        return factories.ActualTypeFactory(*args, **kwargs)
    inner.__name__ = 'create_actual_type'
    return inner


@pytest.fixture
def create_actual(default_owner):
    """
    A fixture that creates a :obj:`Actual` instance using the
    :obj:`ActualFactory`.  Any data that is not explicitly provided will
    be randomly generated by the factory.

    Usage:
    -----
    >>> def test_actual(create_actual):
    >>>     actual = create_actual(description='Test Actual')
    >>>     assert actual.description == 'Test Actual'
    """
    @allow_multiple
    def inner(*args, **kwargs):
        kwargs.setdefault(
            'created_by', default_owner('budget', 'created_by', **kwargs))
        kwargs.setdefault('updated_by', kwargs['created_by'])
        return factories.ActualFactory(*args, **kwargs)
    inner.__name__ = 'create_actual'
    return inner


@pytest.fixture
def create_contact(user):
    """
    A fixture that creates a :obj:`Contact` instance using the
    :obj:`ContactFactory`.  Any data that is not explicitly provided will
    be randomly generated by the factory.

    Usage:
    -----
    >>> def test_contact(create_contact):
    >>>     contact = create_contact(first_name='Jack')
    >>>     assert contact.first_name == 'Jack'
    """
    @allow_multiple
    def inner(*args, **kwargs):
        kwargs.setdefault('created_by', user)
        kwargs.setdefault('updated_by', kwargs['created_by'])
        return factories.ContactFactory(*args, **kwargs)
    inner.__name__ = 'create_contact'
    return inner


@pytest.fixture
def create_header_template(user):
    """
    A fixture that creates a :obj:`HeaderTemplate` instance using the
    :obj:`HeaderTemplateFactory`.  Any data that is not explicitly provided will
    be randomly generated by the factory.

    Usage:
    -----
    >>> def test_create_header_template(create_header_template):
    >>>     template = create_header_template()
    >>>     assert template.left_image is None
    """
    def inner(*args, **kwargs):
        kwargs.setdefault('created_by', user)
        return factories.HeaderTemplateFactory(*args, **kwargs)
    inner.__name__ = 'create_header_template'
    return inner


@pytest.fixture
def all_fixture_factories(
    create_attachment,
    create_color,
    create_user,
    create_public_token,
    create_collaborator,
    create_template,
    create_budget,
    create_account,
    create_subaccount,
    create_budget_subaccount,
    create_budget_account,
    create_template_subaccount,
    create_template_account,
    create_markup,
    create_fringe,
    create_group,
    create_header_template,
    create_subaccount_unit,
    create_actual_type,
    create_actual,
    create_contact
):
    return [
        create_attachment,
        create_color,
        create_user,
        create_public_token,
        create_collaborator,
        create_template,
        create_budget,
        create_account,
        create_subaccount,
        create_budget_subaccount,
        create_budget_account,
        create_template_subaccount,
        create_template_account,
        create_markup,
        create_fringe,
        create_group,
        create_header_template,
        create_subaccount_unit,
        create_actual_type,
        create_actual,
        create_contact
    ]


@pytest.fixture
def f(all_fixture_factories):
    class F:
        def __init__(self):
            # pylint:disable=not-an-iterable
            for f in all_fixture_factories:
                setattr(self, f.__name__, f)
    return F()


CONTEXT_BUDGETS = {
    'budget': Budget,
    'template': Template
}


@pytest.fixture
def budget_factories(create_budget, create_account, create_subaccount):
    class BudgetFactories:
        def __init__(self, domain):
            self.domain = domain
            self.budget_cls = CONTEXT_BUDGETS[self.domain]

        @property
        def account_cls(self):
            return self.budget_cls.account_cls

        @property
        def subaccount_cls(self):
            return self.budget_cls.subaccount_cls

        def create_budget(self, *args, **kwargs):
            kwargs.setdefault('domain', self.domain)
            return create_budget(*args, **kwargs)

        def create_account(self, *args, **kwargs):
            kwargs.setdefault('domain', self.domain)
            return create_account(*args, **kwargs)

        def create_subaccount(self, *args, **kwargs):
            kwargs.setdefault('domain', self.domain)
            return create_subaccount(*args, **kwargs)

    def inner(param):
        return BudgetFactories(param)
    return inner


@pytest.fixture(params=["budget", "template"])
def budget_f(request, budget_factories):
    markers = request.node.own_markers
    marker_names = [m.name for m in markers]
    if 'budget' not in marker_names and 'template' not in marker_names:
        marker_names = marker_names + ['budget', 'template']

    if request.param in marker_names:
        yield budget_factories(request.param)
    else:
        pytest.skip("Test is not applicable for `%s` domain." % request.param)
