import pytest

from django.db import IntegrityError


@pytest.mark.parametrize('context', ['budget', 'template'])
def test_subaccount_fringes_change(create_account, create_context_budget,
        create_fringe, create_subaccount, models, context):
    budget = create_context_budget(context=context)
    account = create_account(parent=budget, context=context)
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
    subaccount = create_subaccount(
        parent=account,
        fringes=fringes,
        quantity=1,
        rate=100,
        context=context
    )
    assert account.nominal_value + account.accumulated_fringe_contribution == 225.0  # noqa
    assert subaccount.nominal_value + subaccount.fringe_contribution == 225.0

    subaccount.fringes.remove(fringes[0])
    assert account.nominal_value + account.accumulated_fringe_contribution == 200.0  # noqa
    assert subaccount.nominal_value + subaccount.fringe_contribution == 200.0


@pytest.mark.parametrize('context', ['budget', 'template'])
def test_subaccount_fringe_changed(create_account, create_context_budget,
        create_fringe, create_subaccount, models, context):
    budget = create_context_budget(context=context)
    account = create_account(parent=budget, context=context)
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
    subaccount = create_subaccount(
        parent=account,
        fringes=fringes,
        quantity=1,
        rate=100,
        context=context
    )
    assert account.nominal_value + account.accumulated_fringe_contribution == 225.0  # noqa
    assert subaccount.nominal_value + subaccount.fringe_contribution == 225.0

    fringes[1].rate = 200.0
    fringes[1].save()

    account.refresh_from_db()
    assert account.nominal_value + account.accumulated_fringe_contribution == 325.0  # noqa

    subaccount.refresh_from_db()
    assert subaccount.nominal_value + subaccount.fringe_contribution == 325.0


@pytest.mark.parametrize('context', ['budget', 'template'])
def test_subaccount_fringe_deleted(create_account, create_context_budget,
        create_fringe, create_subaccount, models, context):
    budget = create_context_budget(context=context)
    account = create_account(parent=budget, context=context)
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
    subaccount = create_subaccount(
        parent=account,
        fringes=fringes,
        quantity=1,
        rate=100,
        context=context
    )
    assert account.nominal_value + account.accumulated_fringe_contribution == 225.0  # noqa
    assert subaccount.nominal_value + subaccount.fringe_contribution == 225.0

    fringes[1].delete()

    account.refresh_from_db()
    assert account.nominal_value + account.accumulated_fringe_contribution == 125.0  # noqa

    subaccount.refresh_from_db()
    assert subaccount.nominal_value + subaccount.fringe_contribution == 125.0


@pytest.mark.parametrize('context', ['budget', 'template'])
def test_fringes_parent_constraint(create_subaccount, create_context_budget,
        create_account, create_fringe, context):
    budget = create_context_budget(context=context)
    another_budget = create_context_budget(context=context)
    account = create_account(parent=budget, context=context)
    subaccount = create_subaccount(parent=account, context=context)
    fringes = [
        create_fringe(budget=another_budget),
        create_fringe(budget=budget)
    ]
    with pytest.raises(IntegrityError):
        subaccount.fringes.set(fringes)
