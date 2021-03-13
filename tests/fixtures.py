import pytest

from greenbudget.management.factories import (
    UserFactory, BudgetFactory, AccountFactory, SubAccountFactory,
    ActualFactory, CommentFactory, ContactFactory)


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
    def inner(*args, **kwargs):
        return UserFactory(*args, **kwargs)
    return inner


@pytest.fixture
def create_budget(user, db):
    """
    A fixture that creates a :obj:`Budget` instance using the
    :obj:`BudgetFactory`.  Any data that is not explicitly provided will
    be randomly generated by the factory.

    Usage:
    -----
    >>> def test_budget(create_budget):
    >>>     budget = create_budget(name='Test Budget')
    >>>     assert budget.name == 'Test Budget'
    """
    def inner(*args, **kwargs):
        kwargs.setdefault('author', user)
        return BudgetFactory(*args, **kwargs)
    return inner


@pytest.fixture
def create_account(user, db):
    """
    A fixture that creates a :obj:`Account` instance using the
    :obj:`AccountFactory`.  Any data that is not explicitly provided will
    be randomly generated by the factory.

    Usage:
    -----
    >>> def test_account(create_account):
    >>>     account = create_account(description='Test Account')
    >>>     assert account.description == 'Test Account'
    """
    def inner(*args, **kwargs):
        kwargs.setdefault('created_by', user)
        kwargs.setdefault('updated_by', user)
        return AccountFactory(*args, **kwargs)
    return inner


@pytest.fixture
def create_sub_account(user, db):
    """
    A fixture that creates a :obj:`SubAccount` instance using the
    :obj:`SubAccountFactory`.  Any data that is not explicitly provided will
    be randomly generated by the factory.

    Usage:
    -----
    >>> def test_sub_account(create_sub_account):
    >>>     subaccount = create_sub_account(name='Test Account')
    >>>     assert subaccount.name == 'Test Account'
    """
    def inner(*args, **kwargs):
        kwargs.setdefault('created_by', user)
        kwargs.setdefault('updated_by', user)
        return SubAccountFactory(*args, **kwargs)
    return inner


@pytest.fixture
def create_actual(user, db):
    """
    A fixture that creates a :obj:`Actual` instance using the
    :obj:`ActualFactory`.  Any data that is not explicitly provided will
    be randomly generated by the factory.

    Usage:
    -----
    >>> def test_actual(create_actual):
    >>>     actual = create_actual(vendor='Test Vendor')
    >>>     assert actual.name == 'Test Vendor'
    """
    def inner(*args, **kwargs):
        kwargs.setdefault('created_by', user)
        kwargs.setdefault('updated_by', user)
        return ActualFactory(*args, **kwargs)
    return inner


@pytest.fixture
def create_comment(user, db):
    """
    A fixture that creates a :obj:`Comment` instance using the
    :obj:`CommentFactory`.  Any data that is not explicitly provided will
    be randomly generated by the factory.

    Usage:
    -----
    >>> def test_comment(create_comment):
    >>>     comment = create_comment(text='My Comment')
    >>>     assert comment.text == 'My Comment'
    """
    def inner(*args, **kwargs):
        kwargs.setdefault('user', user)
        return CommentFactory(*args, **kwargs)
    return inner


@pytest.fixture
def create_contact(user, db):
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
    def inner(*args, **kwargs):
        kwargs.setdefault('user', user)
        return ContactFactory(*args, **kwargs)
    return inner