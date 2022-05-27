import datetime
import pytest


def test_delete_account_reestimates(budget_f):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    parent_subaccount = budget_f.create_subaccount(parent=account)
    subaccount = budget_f.create_subaccount(
        parent=parent_subaccount,
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


def test_delete_account_reactualizes(f):
    budget = f.create_budget()
    account = f.create_account(parent=budget)
    parent_subaccount = f.create_subaccount(parent=account)
    subaccount = f.create_subaccount(
        parent=parent_subaccount,
        rate=1,
        multiplier=5,
        quantity=10,
    )
    f.create_actual(owner=subaccount, budget=budget, value=100.0)

    assert budget.actual == 100.0
    assert account.actual == 100.0
    assert parent_subaccount.actual == 100.0
    assert subaccount.actual == 100.0

    account.delete()

    assert budget.actual == 0.0


@pytest.mark.freeze_time
def test_saving_account_saves_budget(freezer, budget_f, user, staff_user,
        set_model_middleware_user):
    freezer.move_to('2017-05-20')
    budget = budget_f.create_budget(created_by=user)
    account = budget_f.create_account(parent=budget)
    freezer.move_to('2019-05-20')

    # There must be an actively authenticated user that is saving the Account
    # in the context of a request in order for the signals to denote the Budget
    # as having been updated by the user.  We can mimic this by setting the
    # user on the model thread.
    set_model_middleware_user(staff_user)
    account.save()

    budget.refresh_from_db()
    assert budget.updated_at == datetime.datetime(
        2019, 5, 20).replace(tzinfo=datetime.timezone.utc)
    assert budget.updated_by == staff_user
