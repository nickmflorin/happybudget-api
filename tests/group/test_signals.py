import pytest

from django.db import IntegrityError


@pytest.mark.parametrize('context', ['budget', 'template'])
def test_account_group_parent_constraint(create_account, create_context_budget,
        create_group, context):
    budget = create_context_budget(context=context)
    another_budget = create_context_budget(context=context)
    group = create_group(parent=budget)
    with pytest.raises(IntegrityError):
        create_account(parent=another_budget, group=group, context=context)


@pytest.mark.parametrize('context', ['budget', 'template'])
def test_subaccount_group_parent_constraint(create_subaccount,
        create_account, create_context_budget, create_group, context):
    budget = create_context_budget(context=context)
    account = create_account(parent=budget, context=context)
    another_account = create_account(parent=budget, context=context)
    group = create_group(parent=account)
    with pytest.raises(IntegrityError):
        create_subaccount(parent=another_account, group=group, context=context)


@pytest.mark.parametrize('context', ['budget', 'template'])
def test_remove_account_from_group_group_deleted(create_context_budget, models,
        create_group, create_account, context):
    budget = create_context_budget(context=context)
    group = create_group(parent=budget)
    account = create_account(parent=budget, context=context, group=group)
    account.group = None
    account.save()
    assert models.Group.objects.first() is None


@pytest.mark.parametrize('context', ['budget', 'template'])
def test_remove_account_from_group_group_not_deleted(create_context_budget,
        create_account, create_group, models, context):
    budget = create_context_budget(context=context)
    group = create_group(parent=budget)
    account = create_account(parent=budget, group=group, context=context)
    create_account(parent=budget, group=group, context=context)
    account.group = None
    account.save()
    assert models.Group.objects.first() == group


@pytest.mark.parametrize('context', ['budget', 'template'])
def test_remove_subaccount_from_group_group_deleted(create_context_budget,
        create_account, create_group, models, create_subaccount, context):
    budget = create_context_budget(context=context)
    account = create_account(parent=budget, context=context)
    group = create_group(parent=account)
    subaccount = create_subaccount(
        context=context,
        parent=account,
        group=group
    )
    subaccount.group = None
    subaccount.save()
    assert models.Group.objects.first() is None


@pytest.mark.parametrize('context', ['budget', 'template'])
def test_remove_subaccount_from_group_group_not_deleted(create_context_budget,
        create_subaccount, create_account, models, create_group, context):
    budget = create_context_budget(context=context)
    account = create_account(parent=budget, context=context)
    group = create_group(parent=account)
    subaccount = create_subaccount(
        parent=account,
        group=group,
        context=context
    )
    create_subaccount(parent=account, group=group, context=context)
    subaccount.group = None
    subaccount.save()
    assert models.Group.objects.first() == group
