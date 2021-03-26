from django.db import IntegrityError
import pytest

from greenbudget.app.subaccount.models import SubAccountGroup


@pytest.mark.freeze_time('2020-01-01')
def test_group_parent_constraint(create_sub_account, create_account,
        create_budget, create_sub_account_group):
    budget = create_budget()
    account = create_account(budget=budget)
    another_account = create_account(budget=budget)
    group = create_sub_account_group(parent=account)
    with pytest.raises(IntegrityError):
        create_sub_account(
            parent=another_account,
            budget=budget,
            group=group
        )


def test_remove_from_group_group_deleted(create_sub_account, create_account,
        create_budget, create_sub_account_group):
    budget = create_budget()
    account = create_account(budget=budget)
    group = create_sub_account_group(parent=account)
    subaccount = create_sub_account(budget=budget, parent=account, group=group)

    subaccount.group = None
    subaccount.save()

    assert SubAccountGroup.objects.first() is None


def test_remove_from_group_group_not_deleted(create_sub_account, create_account,
        create_budget, create_sub_account_group):
    budget = create_budget()
    account = create_account(budget=budget)
    group = create_sub_account_group(parent=account)
    subaccount = create_sub_account(budget=budget, parent=account, group=group)
    create_sub_account(budget=budget, parent=account, group=group)

    subaccount.group = None
    subaccount.save()

    assert SubAccountGroup.objects.first() == group
