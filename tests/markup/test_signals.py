from django.db import IntegrityError
import pytest


def test_markup_changed_to_flat(budget_f, create_markup, models):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    budget_f.create_subaccount(
        parent=account,
        quantity=10,
        multiplier=4,
        rate=10,
        count=2
    )
    assert account.nominal_value == 800.0
    assert account.markup_contribution == 0.0
    markups = [
        create_markup(
            parent=budget,
            accounts=[account],
            rate=0.5,
            percent=True
        ),
        create_markup(
            parent=budget,
            accounts=[account],
            rate=0.5,
            percent=True
        )
    ]
    account.refresh_from_db()
    assert account.nominal_value == 800.0
    assert account.markup_contribution == 800.0
    assert account.accumulated_markup_contribution == 0.0

    budget.refresh_from_db()
    assert budget.nominal_value == 800.0
    assert budget.accumulated_markup_contribution == 800.0

    markups[0].refresh_from_db()
    markups[0].unit = models.Markup.UNITS.flat
    markups[0].save()

    markups[0].refresh_from_db()
    assert markups[0].children.count() == 0, \
        "The Markup's children were not removed."

    account.refresh_from_db()
    assert account.nominal_value == 800.0
    assert account.markup_contribution == 400.0
    assert account.accumulated_markup_contribution == 0.0

    budget.refresh_from_db()
    assert budget.nominal_value == 800.0
    assert budget.accumulated_markup_contribution == 400.5


def test_account_markups_change(budget_f, create_markup):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    budget_f.create_subaccount(parent=account, quantity=10, rate=10)
    markups = [
        create_markup(
            parent=budget,
            accounts=[account],
            rate=0.5,
            percent=True,
        ),
        create_markup(
            parent=budget,
            accounts=[account],
            rate=0.6,
            percent=True
        )
    ]
    account.refresh_from_db()
    assert account.nominal_value == 100.0
    assert account.markup_contribution == 110.0

    budget.refresh_from_db()
    assert budget.nominal_value == 100.0
    assert budget.accumulated_markup_contribution == 110.0

    account.markups.remove(markups[0])
    assert account.nominal_value == 100.0
    assert account.markup_contribution == 60.0

    budget.refresh_from_db()
    assert budget.nominal_value == 100.0
    assert budget.accumulated_markup_contribution == 60.0


def test_subaccount_markups_change(budget_f, create_markup):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    subaccounts = budget_f.create_subaccount(
        count=2,
        parent=account,
        quantity=10,
        rate=10
    )
    markups = [
        create_markup(
            parent=account,
            subaccounts=subaccounts,
            rate=0.5,
            percent=True,
        ),
        create_markup(
            parent=account,
            subaccounts=[subaccounts[0]],
            rate=0.6,
            percent=True
        )
    ]
    subaccounts[0].refresh_from_db()
    assert subaccounts[0].nominal_value == 100.0
    assert subaccounts[0].markup_contribution == 110.0

    subaccounts[1].refresh_from_db()
    assert subaccounts[1].nominal_value == 100.0
    assert subaccounts[1].markup_contribution == 50.0

    account.refresh_from_db()
    assert account.nominal_value == 200.0
    assert account.markup_contribution == 0.0
    assert account.accumulated_markup_contribution == 160.0

    budget.refresh_from_db()
    assert budget.nominal_value == 200.0
    assert budget.accumulated_markup_contribution == 160.0

    subaccounts[0].markups.remove(markups[1])

    subaccounts[0].refresh_from_db()
    assert subaccounts[0].nominal_value == 100.0
    assert subaccounts[0].markup_contribution == 50.0

    subaccounts[1].refresh_from_db()
    assert subaccounts[1].nominal_value == 100.0
    assert subaccounts[1].markup_contribution == 50.0

    assert account.nominal_value == 200.0
    assert account.markup_contribution == 0.0
    assert account.accumulated_markup_contribution == 100.0

    budget.refresh_from_db()
    assert budget.nominal_value == 200.0
    assert budget.accumulated_markup_contribution == 100.0


def test_account_markup_changes_rate(budget_f, create_markup):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    budget_f.create_subaccount(parent=account, quantity=10, rate=10)
    markups = [
        create_markup(
            parent=budget,
            accounts=[account],
            rate=0.5,
            percent=True,
        ),
        create_markup(
            parent=budget,
            accounts=[account],
            rate=0.6,
            percent=True
        )
    ]
    account.refresh_from_db()
    assert account.nominal_value == 100.0
    assert account.markup_contribution == 110.0

    budget.refresh_from_db()
    assert budget.nominal_value == 100.0
    assert budget.accumulated_markup_contribution == 110.0

    markups[0].rate = 0.7
    markups[0].save()

    account.refresh_from_db()
    assert account.nominal_value == 100.0
    assert account.markup_contribution == 130.0

    budget.refresh_from_db()
    assert budget.nominal_value == 100.0
    assert budget.accumulated_markup_contribution == 130.0


def test_account_markup_changes_unit(budget_f, create_markup, models):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    budget_f.create_subaccount(parent=account, quantity=10, rate=10)
    markups = [
        create_markup(
            parent=budget,
            accounts=[account],
            rate=0.5,
            percent=True,
        ),
        create_markup(
            parent=budget,
            accounts=[account],
            rate=0.6,
            percent=True
        )
    ]
    account.refresh_from_db()
    assert account.nominal_value == 100.0
    assert account.markup_contribution == 110.0

    budget.refresh_from_db()
    assert budget.nominal_value == 100.0
    assert budget.accumulated_markup_contribution == 110.0

    markups[0].unit = models.Markup.UNITS.flat
    markups[0].save()

    assert markups[0].children.count() == 0

    account.refresh_from_db()
    assert account.nominal_value == 100.0
    assert account.markup_contribution == 60.0

    budget.refresh_from_db()
    assert budget.nominal_value == 100.0
    assert budget.accumulated_markup_contribution == 60.5


def test_account_markup_deleted(budget_f, create_markup):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    budget_f.create_subaccount(
        parent=account,
        quantity=10,
        multiplier=4,
        rate=10,
        count=2
    )
    markups = [
        create_markup(
            parent=budget,
            accounts=[account],
            rate=0.5,
            percent=True
        ),
        create_markup(
            parent=budget,
            accounts=[account],
            rate=0.5,
            percent=True
        )
    ]
    account.refresh_from_db()
    assert account.nominal_value == 800.0
    assert account.markup_contribution == 800.0

    markups[0].delete()
    account.refresh_from_db()
    assert account.nominal_value == 800.0
    assert account.markup_contribution == 400.0


def test_subaccount_markup_deleted(budget_f, create_markup):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    subaccount = budget_f.create_subaccount(
        parent=account,
        quantity=10,
        multiplier=4,
        rate=10
    )
    markups = [
        create_markup(
            parent=account,
            subaccounts=[subaccount],
            rate=0.5,
            percent=True
        ),
        create_markup(
            parent=account,
            subaccounts=[subaccount],
            rate=0.5,
            percent=True
        )
    ]
    subaccount.refresh_from_db()
    assert subaccount.nominal_value == 400.0
    assert subaccount.markup_contribution == 400.0

    account.refresh_from_db()
    assert account.nominal_value == 400.0
    assert account.accumulated_markup_contribution == 400.0

    markups[0].delete()

    subaccount.refresh_from_db()
    assert subaccount.nominal_value == 400.0
    assert subaccount.markup_contribution == 200.0

    account.refresh_from_db()
    assert account.nominal_value == 400.0
    assert account.accumulated_markup_contribution == 200.0


def test_account_markup_children_constraint(budget_f, create_markup):
    budget = budget_f.create_budget()
    another_budget = budget_f.create_budget()
    account = budget_f.create_account(parent=another_budget)
    with pytest.raises(IntegrityError):
        create_markup(parent=budget, accounts=[account])


def test_subaccount_markup_children_constraint(budget_f, create_markup):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    another_account = budget_f.create_account(parent=budget)
    subaccount = budget_f.create_subaccount(parent=another_account)
    with pytest.raises(IntegrityError):
        create_markup(parent=account, subaccounts=[subaccount])
