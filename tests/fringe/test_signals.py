import pytest

from django.db import IntegrityError


def test_budget_subaccount_fringes_change(create_budget_account, create_budget,
        create_fringe, create_budget_subaccount, models):
    budget = create_budget()
    account = create_budget_account(parent=budget)
    fringes = [
        create_fringe(
            budget=budget,
            cutoff=50,
            rate=0.5,
            unit=models.Fringe.UNITS.percent
        ),
        create_fringe(
            budget=budget,
            rate=100,
            unit=models.Fringe.UNITS.flat
        ),
    ]
    subaccount = create_budget_subaccount(
        parent=account,
        fringes=fringes,
        quantity=1,
        rate=100
    )
    assert account.real_estimated == 225.0
    assert subaccount.real_estimated == 225.0

    subaccount.fringes.remove(fringes[0])
    assert account.real_estimated == 200.0
    assert subaccount.real_estimated == 200.0


def test_budget_subaccount_fringe_changed(create_budget_account, create_budget,
        create_fringe, create_budget_subaccount, models):
    budget = create_budget()
    account = create_budget_account(parent=budget)
    fringes = [
        create_fringe(
            budget=budget,
            cutoff=50,
            rate=0.5,
            unit=models.Fringe.UNITS.percent
        ),
        create_fringe(
            budget=budget,
            rate=100,
            unit=models.Fringe.UNITS.flat
        ),
    ]
    subaccount = create_budget_subaccount(
        parent=account,
        fringes=fringes,
        quantity=1,
        rate=100
    )
    assert account.real_estimated == 225.0
    assert subaccount.real_estimated == 225.0

    fringes[1].rate = 200.0
    fringes[1].save()

    account.refresh_from_db()
    assert account.real_estimated == 325.0

    subaccount.refresh_from_db()
    assert subaccount.real_estimated == 325.0


def test_budget_subaccount_fringe_deleted(create_budget_account, create_budget,
        create_fringe, create_budget_subaccount, models):
    budget = create_budget()
    account = create_budget_account(parent=budget)
    fringes = [
        create_fringe(
            budget=budget,
            cutoff=50,
            rate=0.5,
            unit=models.Fringe.UNITS.percent
        ),
        create_fringe(
            budget=budget,
            rate=100,
            unit=models.Fringe.UNITS.flat
        ),
    ]
    subaccount = create_budget_subaccount(
        parent=account,
        fringes=fringes,
        quantity=1,
        rate=100
    )
    assert account.real_estimated == 225.0
    assert subaccount.real_estimated == 225.0

    fringes[1].delete()

    account.refresh_from_db()
    assert account.real_estimated == 125.0

    subaccount.refresh_from_db()
    assert subaccount.real_estimated == 125.0


def test_fringes_parent_constraint(create_budget_subaccount, create_budget,
        create_budget_account, create_fringe):
    budget = create_budget()
    another_budget = create_budget()
    account = create_budget_account(parent=budget)
    subaccount = create_budget_subaccount(parent=account)
    fringes = [
        create_fringe(budget=another_budget),
        create_fringe(budget=budget)
    ]
    with pytest.raises(IntegrityError):
        subaccount.fringes.set(fringes)
