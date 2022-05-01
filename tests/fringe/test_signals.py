import pytest

from django.db import IntegrityError


def test_subaccount_fringes_change(budget_f, f, models):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    fringes = [
        f.create_fringe(
            budget=budget,
            cutoff=50,
            rate=0.5,
            unit=models.Fringe.UNITS.percent
        ),
        f.create_fringe(
            budget=budget,
            rate=100,
            unit=models.Fringe.UNITS.flat
        ),
    ]
    subaccount = budget_f.create_subaccount(
        parent=account,
        fringes=fringes,
        quantity=1,
        rate=100
    )
    assert account.nominal_value + account.accumulated_fringe_contribution \
        == 225.0
    assert subaccount.nominal_value + subaccount.fringe_contribution == 225.0

    subaccount.fringes.remove(fringes[0])
    assert account.nominal_value + account.accumulated_fringe_contribution \
        == 200.0
    assert subaccount.nominal_value + subaccount.fringe_contribution == 200.0


def test_subaccount_fringe_changed(budget_f, f, models):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    fringes = [
        f.create_fringe(
            budget=budget,
            cutoff=50,
            rate=0.5,
            unit=models.Fringe.UNITS.percent
        ),
        f.create_fringe(
            budget=budget,
            rate=100,
            unit=models.Fringe.UNITS.flat
        ),
    ]
    subaccount = budget_f.create_subaccount(
        parent=account,
        fringes=fringes,
        quantity=1,
        rate=100
    )
    assert account.nominal_value + account.accumulated_fringe_contribution \
        == 225.0
    assert subaccount.nominal_value + subaccount.fringe_contribution == 225.0

    fringes[1].rate = 200.0
    fringes[1].save()

    account.refresh_from_db()
    assert account.nominal_value + account.accumulated_fringe_contribution \
        == 325.0

    subaccount.refresh_from_db()
    assert subaccount.nominal_value + subaccount.fringe_contribution == 325.0


def test_subaccount_fringe_deleted(budget_f, f, models):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    fringes = [
        f.create_fringe(
            budget=budget,
            cutoff=50,
            rate=0.5,
            unit=models.Fringe.UNITS.percent
        ),
        f.create_fringe(
            budget=budget,
            rate=100,
            unit=models.Fringe.UNITS.flat
        ),
    ]
    subaccount = budget_f.create_subaccount(
        parent=account,
        fringes=fringes,
        quantity=1,
        rate=100
    )
    assert account.nominal_value + account.accumulated_fringe_contribution \
        == 225.0
    assert subaccount.nominal_value + subaccount.fringe_contribution == 225.0

    fringes[1].delete()

    account.refresh_from_db()
    assert account.nominal_value + account.accumulated_fringe_contribution \
        == 125.0

    subaccount.refresh_from_db()
    assert subaccount.nominal_value + subaccount.fringe_contribution == 125.0


def test_fringes_parent_constraint(budget_f, f):
    budget = budget_f.create_budget()
    another_budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    subaccount = budget_f.create_subaccount(parent=account)
    fringes = [
        f.create_fringe(budget=another_budget),
        f.create_fringe(budget=budget)
    ]
    with pytest.raises(IntegrityError):
        subaccount.fringes.set(fringes)
