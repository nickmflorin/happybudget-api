import datetime
from datetime import timezone
import pytest


@pytest.mark.parametrize('context', ['budget', 'template'])
def test_delete_account_reestimates(create_context_budget, create_account,
        create_subaccount, context):
    budget = create_context_budget(context=context)
    account = create_account(parent=budget, context=context)
    parent_subaccount = create_subaccount(parent=account, context=context)
    subaccount = create_subaccount(
        parent=parent_subaccount,
        context=context,
        rate=1,
        multiplier=5,
        quantity=10,
    )
    assert parent_subaccount.nominal_value == 50.0
    assert subaccount.nominal_value == 50.0
    assert account.nominal_value == 50.0
    assert budget.nominal_value == 50.0

    account.delete()
    assert budget.nominal_value == 0.0


def test_delete_account_reactualizes(create_budget, create_budget_account,
        create_budget_subaccount, create_actual):
    budget = create_budget()
    account = create_budget_account(parent=budget)
    parent_subaccount = create_budget_subaccount(parent=account)
    subaccount = create_budget_subaccount(
        parent=parent_subaccount,
        rate=1,
        multiplier=5,
        quantity=10,
    )
    create_actual(owner=subaccount, budget=budget, value=100.0)

    assert budget.actual == 100.0
    assert account.actual == 100.0
    assert parent_subaccount.actual == 100.0
    assert subaccount.actual == 100.0

    account.delete()

    assert budget.actual == 0.0


@pytest.mark.freeze_time
@pytest.mark.parametrize('context', ['budget', 'template'])
def test_saving_subaccount_saves_budget(create_context_budget, create_account,
        freezer, context):
    freezer.move_to('2017-05-20')
    budget = create_context_budget(context=context)
    account = create_account(parent=budget, context=context)
    freezer.move_to('2019-05-20')
    account.save()
    budget.refresh_from_db()
    assert budget.updated_at == datetime.datetime(
        2019, 5, 20).replace(tzinfo=timezone.utc)
