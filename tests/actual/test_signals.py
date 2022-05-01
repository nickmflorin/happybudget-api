def test_create_actual_recalculates(f):
    budget = f.create_budget()
    account = f.create_budget_account(parent=budget)
    subaccount = f.create_budget_subaccount(parent=account)
    f.create_actual(owner=subaccount, budget=budget, value=10)

    subaccount.refresh_from_db()
    assert subaccount.actual == 10.0

    account.refresh_from_db()
    assert account.actual == 10.0

    budget.refresh_from_db()
    assert budget.actual == 10.0


def test_delete_actual_recalculates(f):
    budget = f.create_budget()
    account = f.create_budget_account(parent=budget)
    subaccount = f.create_budget_subaccount(parent=account)
    actual = f.create_actual(owner=subaccount, budget=budget, value=10)

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


def test_change_actual_owner_type_recalculates(f):
    budget = f.create_budget()
    account = f.create_budget_account(parent=budget)
    subaccount = f.create_budget_subaccount(parent=account)
    markup = f.create_markup(parent=account)
    actual = f.create_actual(owner=subaccount, budget=budget, value=10)

    actual.owner = markup
    actual.save()

    subaccount.refresh_from_db()
    assert subaccount.actual == 0.0

    markup.refresh_from_db()
    assert markup.actual == 10.0


def test_change_actual_owner_recalculates(f):
    budget = f.create_budget()
    account = f.create_budget_account(parent=budget)
    subaccount = f.create_budget_subaccount(parent=account)
    actual = f.create_actual(owner=subaccount, budget=budget, value=10)

    another_subaccount = f.create_budget_subaccount(parent=account)
    actual.owner = another_subaccount
    actual.save()

    subaccount.refresh_from_db()
    assert subaccount.actual == 0.0

    another_subaccount.refresh_from_db()
    assert another_subaccount.actual == 10.0

    account.refresh_from_db()
    assert account.actual == 10.0

    budget.refresh_from_db()
    assert budget.actual == 10.0


def test_change_actual_value_recalculates(f):
    budget = f.create_budget()
    account = f.create_budget_account(parent=budget)
    subaccount = f.create_budget_subaccount(parent=account)
    actual = f.create_actual(owner=subaccount, budget=budget, value=10)

    actual.value = 5
    actual.save()

    subaccount.refresh_from_db()
    assert subaccount.actual == 5.0

    account.refresh_from_db()
    assert account.actual == 5.0

    budget.refresh_from_db()
    assert budget.actual == 5.0
