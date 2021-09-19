from django.db import IntegrityError
import pytest

from greenbudget.app import signals


def test_surrounding_markups_removed(create_budget_account, create_budget,
        create_markup, models):
    with signals.disable():
        budget = create_budget()
        accounts = [
            create_budget_account(parent=budget),
            create_budget_account(parent=budget),
            create_budget_account(parent=budget),
            create_budget_account(parent=budget)
        ]
        markups = [
            create_markup(
                parent=budget,
                accounts=[accounts[0]],
                rate=100,
                unit=models.Markup.UNITS.flat
            ),
            create_markup(
                parent=budget,
                accounts=accounts[0:2],
                rate=120,
                unit=models.Markup.UNITS.flat
            ),
            create_markup(
                parent=budget,
                accounts=accounts[0:4],
                rate=120,
                unit=models.Markup.UNITS.flat
            )
        ]
    accounts[0].markups.remove(markups[1])
    assert accounts[0].markups.count() == 1
    assert accounts[0].markups.first() == markups[0]


def test_surrounding_markups_added(create_budget_account, create_budget,
        create_markup, models):
    with signals.disable():
        budget = create_budget()
        accounts = [
            create_budget_account(parent=budget),
            create_budget_account(parent=budget),
            create_budget_account(parent=budget),
            create_budget_account(parent=budget)
        ]
        markups = [
            create_markup(
                parent=budget,
                accounts=[accounts[0]],
                rate=100,
                unit=models.Markup.UNITS.flat
            ),
            create_markup(
                parent=budget,
                accounts=accounts[1:2],
                rate=120,
                unit=models.Markup.UNITS.flat
            ),
            create_markup(
                parent=budget,
                accounts=accounts[2:4],
                rate=120,
                unit=models.Markup.UNITS.flat
            )
        ]
    accounts[0].markups.add(markups[1])
    assert accounts[0].markups.count() == 3


def test_budget_account_markups_change(create_budget_account, create_budget,
        create_markup, create_budget_subaccount, models, lazy):
    budget = create_budget()
    account = create_budget_account(parent=budget, children=[
        lazy(
            factory_fn=create_budget_subaccount,
            quantity=10,
            multiplier=4,
            rate=10
        ),
        lazy(
            factory_fn=create_budget_subaccount,
            quantity=10,
            multiplier=4,
            rate=10
        )
    ])
    markups = [
        create_markup(
            parent=budget,
            accounts=[account],
            rate=100,
            unit=models.Markup.UNITS.flat
        ),
        create_markup(
            parent=budget,
            accounts=[account],
            rate=120,
            unit=models.Markup.UNITS.flat
        )
    ]
    account.refresh_from_db()
    assert account.real_estimated == 1020.0

    account.markups.remove(markups[0])
    assert account.real_estimated == 920.0


def test_budget_account_markup_changes(create_budget_account, create_budget,
        create_markup, create_budget_subaccount, models, lazy):
    budget = create_budget()
    account = create_budget_account(parent=budget, children=[
        lazy(
            factory_fn=create_budget_subaccount,
            quantity=10,
            multiplier=4,
            rate=10
        ),
        lazy(
            factory_fn=create_budget_subaccount,
            quantity=10,
            multiplier=4,
            rate=10
        )
    ])
    markups = [
        create_markup(
            parent=budget,
            accounts=[account],
            rate=100,
            unit=models.Markup.UNITS.flat
        ),
        create_markup(
            parent=budget,
            accounts=[account],
            rate=120,
            unit=models.Markup.UNITS.flat
        )
    ]
    account.refresh_from_db()
    assert account.real_estimated == 1020.0

    markups[0].rate = 50
    markups[0].save()

    account.refresh_from_db()
    assert account.real_estimated == 970.0


def test_budget_subaccount_markups_change(create_budget_account, create_budget,
        create_markup, create_budget_subaccount, models):
    budget = create_budget()
    account = create_budget_account(parent=budget)
    subaccount = create_budget_subaccount(
        parent=account,
        quantity=10,
        multiplier=4,
        rate=10
    )
    markups = [
        create_markup(
            parent=account,
            subaccounts=[subaccount],
            rate=100,
            unit=models.Markup.UNITS.flat
        ),
        create_markup(
            parent=account,
            subaccounts=[subaccount],
            rate=120,
            unit=models.Markup.UNITS.flat
        )
    ]
    subaccount.refresh_from_db()
    assert subaccount.estimated == 400.0
    assert subaccount.real_estimated == 620.0

    account.refresh_from_db()
    assert account.estimated == 400.0
    assert account.real_estimated == 620.0

    subaccount.markups.remove(markups[0])
    assert subaccount.estimated == 400.0
    assert subaccount.real_estimated == 520.0
    assert account.estimated == 400.0
    assert account.real_estimated == 520.0


def test_budget_subaccount_markup_changed(create_budget_account, create_budget,
        create_markup, create_budget_subaccount, models):
    budget = create_budget()
    account = create_budget_account(parent=budget)
    subaccount = create_budget_subaccount(
        parent=account,
        quantity=10,
        multiplier=4,
        rate=10
    )
    markups = [
        create_markup(
            parent=account,
            subaccounts=[subaccount],
            rate=100,
            unit=models.Markup.UNITS.flat
        ),
        create_markup(
            parent=account,
            subaccounts=[subaccount],
            rate=120,
            unit=models.Markup.UNITS.flat
        )
    ]
    subaccount.refresh_from_db()
    assert subaccount.estimated == 400.0
    assert subaccount.real_estimated == 620.0

    account.refresh_from_db()
    assert account.estimated == 400.0
    assert account.real_estimated == 620.0

    markups[0].rate = 50
    markups[0].save()

    subaccount.refresh_from_db()
    assert subaccount.estimated == 400.0
    assert subaccount.real_estimated == 570.0

    account.refresh_from_db()
    assert account.estimated == 400.0
    assert account.real_estimated == 570.0


def test_budget_account_markup_deleted(create_budget_account, create_budget,
        create_markup, create_budget_subaccount, models, lazy):
    budget = create_budget()
    account = create_budget_account(parent=budget, children=[
        lazy(
            factory_fn=create_budget_subaccount,
            quantity=10,
            multiplier=4,
            rate=10
        ),
        lazy(
            factory_fn=create_budget_subaccount,
            quantity=10,
            multiplier=4,
            rate=10
        )
    ])
    markups = [
        create_markup(
            parent=budget,
            accounts=[account],
            rate=100,
            unit=models.Markup.UNITS.flat
        ),
        create_markup(
            parent=budget,
            accounts=[account],
            rate=120,
            unit=models.Markup.UNITS.flat
        )
    ]
    account.refresh_from_db()
    assert account.real_estimated == 1020.0
    markups[0].delete()
    account.refresh_from_db()
    assert account.real_estimated == 920.0


def test_budget_subaccount_markup_deleted(create_budget_account, create_budget,
        create_markup, create_budget_subaccount, models):
    budget = create_budget()
    account = create_budget_account(parent=budget)
    subaccount = create_budget_subaccount(
        parent=account,
        quantity=10,
        multiplier=4,
        rate=10
    )
    markups = [
        create_markup(
            parent=account,
            subaccounts=[subaccount],
            rate=100,
            unit=models.Markup.UNITS.flat
        ),
        create_markup(
            parent=account,
            subaccounts=[subaccount],
            rate=120,
            unit=models.Markup.UNITS.flat
        )
    ]
    subaccount.refresh_from_db()
    assert subaccount.estimated == 400.0
    assert subaccount.real_estimated == 620.0

    account.refresh_from_db()
    assert account.estimated == 400.0
    assert account.real_estimated == 620.0

    markups[0].delete()

    subaccount.refresh_from_db()
    assert subaccount.estimated == 400.0
    assert subaccount.real_estimated == 520.0

    account.refresh_from_db()
    assert account.estimated == 400.0
    assert account.real_estimated == 520.0


def test_budget_account_markup_children_constraint(create_budget_account,
        create_budget, create_markup):
    budget = create_budget()
    another_budget = create_budget()
    account = create_budget_account(parent=another_budget)
    with pytest.raises(IntegrityError):
        create_markup(parent=budget, accounts=[account])


def test_budget_subaccount_markup_children_constraint(create_budget_account,
        create_budget, create_budget_subaccount, create_markup):
    budget = create_budget()
    account = create_budget_account(parent=budget)
    another_account = create_budget_account(parent=budget)
    subaccount = create_budget_subaccount(parent=another_account)
    with pytest.raises(IntegrityError):
        create_markup(parent=account, subaccounts=[subaccount])
