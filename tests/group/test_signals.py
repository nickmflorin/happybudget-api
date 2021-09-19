import pytest

from django.db import IntegrityError


def test_budget_account_group_parent_constraint(create_budget_account,
        create_budget, create_group):
    budget = create_budget()
    another_budget = create_budget()
    group = create_group(parent=budget)
    with pytest.raises(IntegrityError):
        create_budget_account(parent=another_budget, group=group)


def test_template_account_group_parent_constraint(create_template_account,
        create_template, create_group):
    template = create_template()
    another_template = create_template()
    group = create_group(parent=template)
    with pytest.raises(IntegrityError):
        create_template_account(parent=another_template, group=group)


def test_budget_subaccount_group_parent_constraint(create_budget_subaccount,
        create_budget_account, create_budget, create_group):
    budget = create_budget()
    account = create_budget_account(parent=budget)
    another_account = create_budget_account(parent=budget)
    group = create_group(parent=account)
    with pytest.raises(IntegrityError):
        create_budget_subaccount(parent=another_account, group=group)


def test_template_subaccount_group_parent_constraint(create_budget_subaccount,
        create_template_account, create_template, create_group):
    template = create_template()
    account = create_template_account(parent=template)
    another_account = create_template_account(parent=template)
    group = create_group(parent=account)
    with pytest.raises(IntegrityError):
        create_budget_subaccount(parent=another_account, group=group)


def test_remove_budget_account_from_group_group_deleted(create_budget, user,
        create_group, models):
    budget = create_budget()
    group = create_group(parent=budget)
    account = models.BudgetAccount.objects.create(
        parent=budget,
        identifier="Identifier",
        group=group,
        updated_by=user,
        created_by=user
    )
    account.group = None
    account.save()
    assert models.Group.objects.first() is None


def test_remove_template_account_from_group_group_deleted(create_template, user,
        create_group, models):
    template = create_template()
    group = create_group(parent=template)
    account = models.TemplateAccount.objects.create(
        parent=template,
        identifier="Identifier",
        group=group,
        updated_by=user,
        created_by=user
    )
    account.group = None
    account.save()
    assert models.Group.objects.first() is None


def test_remove_budget_account_from_group_group_not_deleted(create_budget,
        create_budget_account, create_group, models):
    budget = create_budget()
    group = create_group(parent=budget)
    account = create_budget_account(parent=budget, group=group)
    create_budget_account(parent=budget, group=group)

    account.group = None
    account.save()
    assert models.Group.objects.first() == group


def test_remove_template_account_from_group_group_not_deleted(create_template,
        create_template_account, create_group, models):
    template = create_template()
    group = create_group(parent=template)
    account = create_template_account(parent=template, group=group)
    create_template_account(parent=template, group=group)

    account.group = None
    account.save()
    assert models.Group.objects.first() == group


def test_remove_budget_subaccount_from_group_group_deleted(user, create_budget,
        create_budget_account, create_group, models):
    budget = create_budget()
    account = create_budget_account(parent=budget)
    group = create_group(parent=account)
    subaccount = models.BudgetSubAccount.objects.create(
        parent=account,
        identifier="Identifier",
        group=group,
        updated_by=user,
        created_by=user
    )
    subaccount.group = None
    subaccount.save()
    assert models.Group.objects.first() is None


def test_remove_template_subaccount_from_group_group_deleted(user, models,
        create_template, create_template_account,
        create_group):
    template = create_template()
    account = create_template_account(parent=template)
    group = create_group(parent=account)
    subaccount = models.TemplateSubAccount.objects.create(
        parent=account,
        identifier="Identifier",
        group=group,
        updated_by=user,
        created_by=user
    )
    subaccount.group = None
    subaccount.save()
    assert models.Group.objects.first() is None


def test_remove_budget_subaccount_from_group_group_not_deleted(create_budget,
        create_budget_subaccount, create_budget_account, models,
        create_group):
    budget = create_budget()
    account = create_budget_account(parent=budget)
    group = create_group(parent=account)
    subaccount = create_budget_subaccount(
        parent=account,
        group=group
    )
    create_budget_subaccount(parent=account, group=group)
    subaccount.group = None
    subaccount.save()
    assert models.Group.objects.first() == group


def test_remove_template_subaccount_from_group_group_not_deleted(models,
        create_template, create_template_subaccount, create_template_account,
        create_group):
    budget = create_template()
    account = create_template_account(parent=budget)
    group = create_group(parent=account)
    subaccount = create_template_subaccount(
        parent=account,
        group=group
    )
    create_template_subaccount(parent=account, group=group)
    subaccount.group = None
    subaccount.save()
    assert models.Group.objects.first() == group
