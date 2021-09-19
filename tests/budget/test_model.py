from greenbudget.app import signals


def test_bulk_create_budgets(models, user):
    instances = [
        models.Budget(name='Budget 1', created_by=user),
        models.Budget(name='Budget 2', created_by=user)
    ]
    created = models.Budget.objects.bulk_create(instances,
        return_created_objects=True)
    assert [b.pk for b in created] == [1, 2]
    assert [b.name for b in created] == ["Budget 1", "Budget 2"]
    assert [b.created_by for b in created] == [user, user]

    assert models.Budget.objects.count() == 2
    assert models.BaseBudget.objects.count() == 2

    budgets = models.Budget.objects.all()
    assert [b.name for b in budgets] == ["Budget 2", "Budget 1"]
    assert all([b.created_by == user] for b in budgets)


def test_duplicate_budget(user, create_budget, create_fringe,
        create_group, create_budget_account, create_budget_subaccount):
    with signals.post_save.disable():
        original = create_budget(created_by=user)
        fringes = [
            create_fringe(
                budget=original,
                created_by=user,
                updated_by=user
            ),
            create_fringe(
                budget=original,
                created_by=user,
                updated_by=user
            ),
        ]
        account_group = create_group(parent=original)
        accounts = [
            create_budget_account(
                parent=original,
                created_by=user,
                updated_by=user,
                group=account_group,
            ),
            create_budget_account(
                parent=original,
                created_by=user,
                updated_by=user,
                group=account_group,
            )
        ]
        subaccount_group = create_group(parent=accounts[0])
        subaccounts = [
            create_budget_subaccount(
                parent=accounts[0],
                created_by=user,
                updated_by=user,
                group=subaccount_group
            ),
            create_budget_subaccount(
                parent=accounts[1],
                created_by=user,
                updated_by=user
            )
        ]
        child_subaccounts = [
            create_budget_subaccount(
                parent=subaccounts[0],
                created_by=user,
                updated_by=user
            ),
            create_budget_subaccount(
                parent=subaccounts[1],
                created_by=user,
                updated_by=user
            )
        ]

    budget = original.duplicate(user)

    assert budget.name == original.name
    assert budget.children.count() == 2
    assert budget.created_by == user

    account_group.refresh_from_db()
    assert budget.groups.count() == 1
    budget_account_group = budget.groups.first()
    assert budget_account_group.name == account_group.name
    assert budget_account_group.color == account_group.color

    assert budget.fringes.count() == 2

    first_fringe = budget.fringes.first()
    assert first_fringe.created_by == user
    assert first_fringe.updated_by == user
    assert first_fringe.name == fringes[0].name
    assert first_fringe.description == fringes[0].description
    assert first_fringe.cutoff == fringes[0].cutoff
    assert first_fringe.rate == fringes[0].rate
    assert first_fringe.unit == fringes[0].unit

    second_fringe = budget.fringes.all()[1]
    assert second_fringe.created_by == user
    assert second_fringe.updated_by == user
    assert second_fringe.name == fringes[1].name
    assert second_fringe.description == fringes[1].description
    assert second_fringe.cutoff == fringes[1].cutoff
    assert second_fringe.rate == fringes[1].rate
    assert second_fringe.unit == fringes[1].unit

    assert budget.children.count() == 2
    first_account = budget.children.first()
    assert first_account.group == budget_account_group
    assert first_account.identifier == accounts[0].identifier
    assert first_account.description == accounts[0].description
    assert first_account.created_by == user
    assert first_account.updated_by == user

    assert first_account.children.count() == 1

    assert first_account.groups.count() == 1
    budget_subaccount_group = first_account.groups.first()
    assert budget_subaccount_group.name == subaccount_group.name
    assert budget_subaccount_group.color == subaccount_group.color

    first_account_subaccount = first_account.children.first()
    assert first_account_subaccount.group == budget_subaccount_group

    assert first_account_subaccount.created_by == user
    assert first_account_subaccount.updated_by == user
    assert first_account_subaccount.identifier == subaccounts[0].identifier
    assert first_account_subaccount.description == subaccounts[0].description

    # These values will be None because the subaccount has children.
    assert first_account_subaccount.rate is None
    assert first_account_subaccount.quantity is None
    assert first_account_subaccount.multiplier is None
    assert first_account_subaccount.unit is None

    assert first_account_subaccount.children.count() == 1
    first_account_subaccount_subaccount = first_account_subaccount.children.first()  # noqa
    assert first_account_subaccount_subaccount.created_by == user
    assert first_account_subaccount_subaccount.updated_by == user
    assert first_account_subaccount_subaccount.identifier == child_subaccounts[0].identifier  # noqa
    assert first_account_subaccount_subaccount.description == child_subaccounts[0].description  # noqa
    assert first_account_subaccount_subaccount.rate == child_subaccounts[0].rate  # noqa
    assert first_account_subaccount_subaccount.quantity == child_subaccounts[0].quantity  # noqa
    assert first_account_subaccount_subaccount.multiplier == child_subaccounts[0].multiplier  # noqa
    assert first_account_subaccount_subaccount.unit == child_subaccounts[0].unit  # noqa

    second_account = budget.children.all()[1]
    assert second_account.group == budget_account_group
    assert second_account.identifier == accounts[1].identifier
    assert second_account.description == accounts[1].description
    assert second_account.created_by == user
    assert second_account.updated_by == user

    assert second_account.children.count() == 1
    second_account_subaccount = second_account.children.first()
    assert second_account_subaccount.created_by == user
    assert second_account_subaccount.updated_by == user
    assert second_account_subaccount.identifier == subaccounts[1].identifier
    assert second_account_subaccount.description == subaccounts[1].description

    # These values will be None because the subaccount has children.
    assert second_account_subaccount.rate is None
    assert second_account_subaccount.quantity is None
    assert second_account_subaccount.multiplier is None
    assert second_account_subaccount.unit is None

    assert second_account_subaccount.children.count() == 1
    second_account_subaccount_subaccount = second_account_subaccount.children.first()  # noqa
    assert second_account_subaccount_subaccount.created_by == user
    assert second_account_subaccount_subaccount.updated_by == user
    assert second_account_subaccount_subaccount.identifier == child_subaccounts[1].identifier  # noqa
    assert second_account_subaccount_subaccount.description == child_subaccounts[1].description  # noqa
    assert second_account_subaccount_subaccount.rate == child_subaccounts[1].rate  # noqa
    assert second_account_subaccount_subaccount.quantity == child_subaccounts[1].quantity  # noqa
    assert second_account_subaccount_subaccount.multiplier == child_subaccounts[1].multiplier  # noqa
    assert second_account_subaccount_subaccount.unit == child_subaccounts[1].unit  # noqa
