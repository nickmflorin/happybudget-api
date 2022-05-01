import pytest

from django.db import IntegrityError


def test_account_group_parent_constraint(budget_f, f):
    budget = budget_f.create_budget()
    another_budget = budget_f.create_budget()
    group = f.create_group(parent=budget)
    with pytest.raises(IntegrityError):
        budget_f.create_account(parent=another_budget, group=group)


def test_subaccount_group_parent_constraint(budget_f, f):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    another_account = budget_f.create_account(parent=budget)
    group = f.create_group(parent=account)
    with pytest.raises(IntegrityError):
        budget_f.create_subaccount(parent=another_account, group=group)


def test_remove_account_from_group_group_deleted(budget_f, models, f):
    budget = budget_f.create_budget()
    group = f.create_group(parent=budget)
    account = budget_f.create_account(parent=budget, group=group)
    account.group = None
    account.save()
    assert models.Group.objects.first() is None


def test_remove_account_from_group_group_not_deleted(budget_f, f, models):
    budget = budget_f.create_budget()
    group = f.create_group(parent=budget)
    account = budget_f.create_account(parent=budget, group=group)
    budget_f.create_account(parent=budget, group=group)
    account.group = None
    account.save()
    assert models.Group.objects.first() == group


def test_remove_subaccount_from_group_group_deleted(budget_f, f, models):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    group = f.create_group(parent=account)
    subaccount = budget_f.create_subaccount(parent=account, group=group)
    subaccount.group = None
    subaccount.save()
    assert models.Group.objects.first() is None


def test_remove_subaccount_from_group_group_not_deleted(budget_f, f, models):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    group = f.create_group(parent=account)
    subaccount = budget_f.create_subaccount(parent=account, group=group)
    budget_f.create_subaccount(parent=account, group=group)
    subaccount.group = None
    subaccount.save()
    assert models.Group.objects.first() == group
