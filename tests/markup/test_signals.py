from django.db import IntegrityError
import pytest


@pytest.mark.parametrize('context', ['budget', 'template'])
def test_markup_changed_to_flat(create_account, create_context_budget,
        create_markup, create_subaccounts, models, context):
    budget = create_context_budget(context=context)
    account = create_account(parent=budget, context=context)
    create_subaccounts(
        parent=account,
        context=context,
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


@pytest.mark.parametrize('context', ['budget', 'template'])
def test_account_markups_change(create_account, create_context_budget,
        create_markup, create_subaccounts, context):
    budget = create_context_budget(context=context)
    account = create_account(parent=budget, context=context)
    create_subaccounts(parent=account, quantity=10, rate=10, context=context)
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


@pytest.mark.parametrize('context', ['budget', 'template'])
def test_subaccount_markups_change(create_account, create_context_budget,
        create_markup, create_subaccounts, context):
    budget = create_context_budget(context=context)
    account = create_account(parent=budget, context=context)
    subaccounts = create_subaccounts(
        context=context,
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


@pytest.mark.parametrize('context', ['budget', 'template'])
def test_account_markup_changes_rate(create_account, create_context_budget,
        create_markup, create_subaccounts, context):
    budget = create_context_budget(context=context)
    account = create_account(parent=budget, context=context)
    create_subaccounts(parent=account, quantity=10, rate=10, context=context)
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


@pytest.mark.parametrize('context', ['budget', 'template'])
def test_account_markup_changes_unit(create_account, create_context_budget,
        create_markup, create_subaccounts, models, context):
    budget = create_context_budget(context=context)
    account = create_account(parent=budget, context=context)
    create_subaccounts(parent=account, quantity=10, rate=10, context=context)
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


@pytest.mark.parametrize('context', ['budget', 'template'])
def test_account_markup_deleted(create_account, create_context_budget,
        create_markup, create_subaccounts, context):
    budget = create_context_budget(context=context)
    account = create_account(parent=budget, context=context)
    create_subaccounts(
        parent=account,
        context=context,
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


@pytest.mark.parametrize('context', ['budget', 'template'])
def test_subaccount_markup_deleted(create_account, create_context_budget,
        create_markup, create_subaccount, context):
    budget = create_context_budget(context=context)
    account = create_account(parent=budget, context=context)
    subaccount = create_subaccount(
        context=context,
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


@pytest.mark.parametrize('context', ['budget', 'template'])
def test_account_markup_children_constraint(create_account, context,
        create_context_budget, create_markup):
    budget = create_context_budget(context=context)
    another_budget = create_context_budget(context=context)
    account = create_account(parent=another_budget, context=context)
    with pytest.raises(IntegrityError):
        create_markup(parent=budget, accounts=[account])


@pytest.mark.parametrize('context', ['budget', 'template'])
def test_subaccount_markup_children_constraint(create_account,
        create_context_budget, create_subaccount, create_markup, context):
    budget = create_context_budget(context=context)
    account = create_account(parent=budget, context=context)
    another_account = create_account(parent=budget, context=context)
    subaccount = create_subaccount(parent=another_account, context=context)
    with pytest.raises(IntegrityError):
        create_markup(parent=account, subaccounts=[subaccount])
