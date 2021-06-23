import pytest

from django.db import IntegrityError


def test_budget_group_parent_constraint(create_budget_subaccount,
        create_budget_account, create_budget, create_budget_subaccount_group):
    budget = create_budget()
    account = create_budget_account(budget=budget)
    another_account = create_budget_account(budget=budget)
    group = create_budget_subaccount_group(parent=account)
    with pytest.raises(IntegrityError):
        create_budget_subaccount(
            parent=another_account,
            budget=budget,
            group=group
        )


def test_fringes_constraint(create_budget_subaccount, create_budget_account,
        create_budget, create_fringe):
    budget = create_budget()
    another_budget = create_budget()
    account = create_budget_account(budget=budget)
    subaccount = create_budget_subaccount(budget=budget, parent=account)
    fringes = [
        create_fringe(budget=another_budget),
        create_fringe(budget=budget)
    ]
    with pytest.raises(IntegrityError):
        subaccount.fringes.set(fringes)


def test_template_group_parent_constraint(create_budget_subaccount,
        create_budget_account, create_budget, create_budget_subaccount_group):
    budget = create_budget()
    account = create_budget_account(budget=budget)
    another_account = create_budget_account(budget=budget)
    group = create_budget_subaccount_group(parent=account)
    with pytest.raises(IntegrityError):
        create_budget_subaccount(
            parent=another_account,
            budget=budget,
            group=group
        )
