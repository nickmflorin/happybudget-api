from happybudget.app import signals
from happybudget.app.subaccount.tasks import fix_corrupted_fringe_relationships


def test_find_and_remove_corrupted_fringe_relationships(f):
    budgets = [
        f.create_budget(),
        f.create_budget(),
    ]
    fringes = [
        f.create_fringe(budget=budgets[0]),
        f.create_fringe(budget=budgets[0]),
        f.create_fringe(budget=budgets[1]),
    ]
    accounts = [
        f.create_account(parent=budgets[0]),
        f.create_account(parent=budgets[1])
    ]

    # Disable the signals so the default validation is ignored and we are able
    # to create the invalid relationships.
    with signals.disable():
        subaccounts = [
            # Should be fixed - Fringe(s) do not all belong to same Budget.
            f.create_subaccount(
                parent=accounts[0],
                fringes=[fringes[0], fringes[2]]
            ),
            # Should be left in tact - Fringe(s) all belong to same Budget.
            f.create_subaccount(
                parent=accounts[0],
                fringes=[fringes[0], fringes[1]]
            ),
            # Should be left in tact, there are no Fringe(s).
            f.create_subaccount(parent=accounts[0]),
            # Should be fixed - Fringe(s) do not all belong to same Budget.
            f.create_subaccount(
                parent=accounts[1],
                fringes=[fringes[0], fringes[2]]
            )
        ]

    fix_corrupted_fringe_relationships()
    assert [f.pk for f in subaccounts[0].fringes.all()] == [fringes[0].pk]
    assert [f.pk for f in subaccounts[1].fringes.all()] \
        == [fringes[0].pk, fringes[1].pk]
    assert [f.pk for f in subaccounts[2].fringes.all()] == []
    assert [f.pk for f in subaccounts[3].fringes.all()] == [fringes[2].pk]
