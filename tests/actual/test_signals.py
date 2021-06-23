from greenbudget.app import signals


def test_create_actual_recalculates(create_budget_account, create_budget,
        create_actual, create_budget_subaccount):
    budget = create_budget()
    account = create_budget_account(budget=budget)
    subaccount = create_budget_subaccount(parent=account, budget=budget)
    create_actual(subaccount=subaccount, budget=budget, value=10)

    subaccount.refresh_from_db()
    assert subaccount.actual == 10.0

    account.refresh_from_db()
    assert account.actual == 10.0

    budget.refresh_from_db()
    assert budget.actual == 10.0


def test_create_actuals_in_bulk_context(create_budget_account, create_budget,
        create_actual, create_budget_subaccount):

    budget = create_budget()
    account = create_budget_account(budget=budget)
    another_account = create_budget_account(budget=budget)
    subaccounts = [
        create_budget_subaccount(parent=account, budget=budget),
        create_budget_subaccount(parent=account, budget=budget),
        create_budget_subaccount(parent=another_account, budget=budget)
    ]

    with signals.bulk_context:
        create_actual(subaccount=subaccounts[0], budget=budget, value=10)
        create_actual(subaccount=subaccounts[1], budget=budget, value=20)
        create_actual(subaccount=subaccounts[1], budget=budget, value=40)
        create_actual(subaccount=subaccounts[2], budget=budget, value=10)
        create_actual(subaccount=subaccounts[2], budget=budget, value=20)
        create_actual(subaccount=subaccounts[2], budget=budget, value=40)

        # Values are not updated yet, because all of the functions will run
        # once we have exited the context.
        assert subaccounts[0].actual == 0.0
        assert subaccounts[1].actual == 0.0
        assert subaccounts[2].actual == 0.0
        assert account.actual == 0.0
        assert budget.actual == 0.0
        assert another_account.actual == 0.0
        assert budget.actual == 0.0

    assert subaccounts[0].actual == 10.0
    assert subaccounts[1].actual == 60.0
    assert subaccounts[2].actual == 70.0
    assert account.actual == 70.0
    assert another_account.actual == 70.0
    assert budget.actual == 140.0


def test_delete_actual_recalculates(create_budget_account, create_budget,
        create_actual, create_budget_subaccount):
    budget = create_budget()
    account = create_budget_account(budget=budget)
    subaccount = create_budget_subaccount(parent=account, budget=budget)
    actual = create_actual(subaccount=subaccount, budget=budget, value=10)

    subaccount.refresh_from_db()
    assert subaccount.actual == 10.0

    account.refresh_from_db()
    assert account.actual == 10.0

    budget.refresh_from_db()
    assert budget.actual == 10.0

    actual.delete()

    subaccount.refresh_from_db()
    assert subaccount.actual == 0.0

    account.refresh_from_db()
    assert account.actual == 0.0

    budget.refresh_from_db()
    assert budget.actual == 0.0


def test_change_actual_subaccount_recalculates(create_budget_account,
        create_budget, create_actual, create_budget_subaccount):
    budget = create_budget()
    account = create_budget_account(budget=budget)
    subaccount = create_budget_subaccount(parent=account, budget=budget)
    actual = create_actual(subaccount=subaccount, budget=budget, value=10)

    another_subaccount = create_budget_subaccount(parent=account, budget=budget)
    actual.subaccount = another_subaccount
    actual.save()

    subaccount.refresh_from_db()
    assert subaccount.actual == 0.0

    another_subaccount.refresh_from_db()
    assert another_subaccount.actual == 10.0

    account.refresh_from_db()
    assert account.actual == 10.0

    budget.refresh_from_db()
    assert budget.actual == 10.0


def test_change_actual_value_recalculates(create_budget_account,
        create_budget, create_actual, create_budget_subaccount):
    budget = create_budget()
    account = create_budget_account(budget=budget)
    subaccount = create_budget_subaccount(parent=account, budget=budget)
    actual = create_actual(subaccount=subaccount, budget=budget, value=10)

    actual.value = 5
    actual.save()

    subaccount.refresh_from_db()
    assert subaccount.actual == 5.0

    account.refresh_from_db()
    assert account.actual == 5.0

    budget.refresh_from_db()
    assert budget.actual == 5.0
