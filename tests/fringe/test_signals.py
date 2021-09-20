def test_create_subaccount_with_fringes_estimates(create_budget,
        create_budget_account, create_budget_subaccount, create_fringe, models):
    budget = create_budget()
    fringes = [
        create_fringe(
            budget=budget,
            cutoff=50,
            rate=0.5,
            unit=models.Fringe.UNITS.percent
        ),
        create_fringe(budget=budget, rate=None),
        create_fringe(
            budget=budget,
            cutoff=20,
            rate=100,
            unit=models.Fringe.UNITS.flat
        ),
        create_fringe(
            budget=budget,
            rate=100,
            unit=models.Fringe.UNITS.flat
        ),
        create_fringe(
            budget=budget,
            rate=0.1,
            unit=models.Fringe.UNITS.percent
        )
    ]
    account = create_budget_account(budget=budget)
    subaccount = create_budget_subaccount(
        parent=account,
        fringes=fringes,
        multiplier=1.0,
        quantity=1.0,
        rate=5.0
    )
    assert subaccount.estimated == 208.0


def test_add_fringe_to_subaccount_estimates(create_budget,
        create_budget_account, create_budget_subaccount, create_fringe, models):
    budget = create_budget()
    account = create_budget_account(budget=budget)
    subaccount = create_budget_subaccount(
        parent=account,
        multiplier=1.0,
        quantity=1.0,
        rate=5.0
    )
    assert subaccount.estimated == 5.0
    fringe = create_fringe(
        budget=budget,
        cutoff=50,
        rate=0.5,
        unit=models.Fringe.UNITS.percent
    )
    subaccount.fringes.add(fringe)
    assert subaccount.estimated == 7.5


def test_subacount_fringe_changes_restimates(create_budget,
        create_budget_account, create_budget_subaccount, create_fringe, models):
    budget = create_budget()
    account = create_budget_account(budget=budget)
    subaccount = create_budget_subaccount(
        parent=account,
        multiplier=1.0,
        quantity=1.0,
        rate=5.0
    )
    assert subaccount.estimated == 5.0
    fringe = create_fringe(
        budget=budget,
        cutoff=50,
        rate=0.5,
        unit=models.Fringe.UNITS.percent
    )
    subaccount.fringes.add(fringe)
    assert subaccount.estimated == 7.5
    fringe.rate = 0.6
    fringe.save()

    subaccount.refresh_from_db()
    assert subaccount.estimated == 8.0
