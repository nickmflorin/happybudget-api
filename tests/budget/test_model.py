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


def test_duplicate_budget(user, create_budget, create_fringe, create_markup,
        create_group, create_budget_account, create_budget_subaccount,
        create_actual):
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
        budget_markups = [
            create_markup(parent=original),
            create_markup(parent=original)
        ]
        account_group = create_group(parent=original)
        accounts = [
            create_budget_account(
                parent=original,
                markups=budget_markups,
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
        account_markups = [
            create_markup(parent=accounts[0]),
            create_markup(parent=accounts[0])
        ]
        subaccount_group = create_group(parent=accounts[0])
        subaccounts = [
            create_budget_subaccount(
                parent=accounts[0],
                markups=account_markups,
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
        actuals = [
            create_actual(owner=budget_markups[0], budget=original),
            create_actual(owner=account_markups[1], budget=original),
            create_actual(owner=subaccounts[0], budget=original),
            create_actual(owner=child_subaccounts[1], budget=original)
        ]

    budget = original.duplicate(user)

    assert budget.name == original.name
    assert budget.children.count() == 2
    assert budget.created_by == user
    assert budget.children_markups.count() == 2

    account_group.refresh_from_db()
    assert budget.groups.count() == 1
    budget_account_group = budget.groups.first()
    assert budget_account_group.name == account_group.name
    assert budget_account_group.color == account_group.color

    assert budget.actuals.count() == 4
    ASSERT_ACTUAL_FIELDS = (
        'purchase_order', 'description', 'date', 'payment_id', 'value',
        'payment_method'
    )
    for i, actual in enumerate(budget.actuals.all()):
        actuals[i].refresh_from_db()
        for field in ASSERT_ACTUAL_FIELDS:
            assert getattr(actual, field) == getattr(actuals[i], field), \
                "Actual number %s differs in field %s." % (i, field)
            assert actual.created_by == user
            assert actual.updated_by == user
            assert actual.budget == budget
            assert actual.owner is not None

    assert budget.fringes.count() == 2
    ASSERT_FRINGE_FIELDS = ('rate', 'unit', 'name', 'description', 'cutoff')
    for i, fringe in enumerate(budget.fringes.all()):
        fringes[i].refresh_from_db()
        for field in ASSERT_FRINGE_FIELDS:
            assert getattr(fringe, field) == getattr(fringes[i], field), \
                "Fringe number %s differs in field %s." % (i, field)
            assert fringe.created_by == user
            assert fringe.updated_by == user

    ASSERT_SUBACCOUNT_FIELDS = (
        'identifier', 'description', 'rate', 'quantity', 'multiplier', 'unit'
    )

    def compare_subaccounts(a, b):
        for field in ASSERT_SUBACCOUNT_FIELDS:
            assert getattr(a, field) == getattr(b, field), \
                "Sub accounts differ in field %s." % field

    assert budget.children.count() == 2
    first_account = budget.children.first()
    assert first_account.markups.count() == 2
    assert first_account.children_markups.count() == 2
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
    assert first_account_subaccount.markups.count() == 2
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
    compare_subaccounts(
        first_account_subaccount_subaccount,
        child_subaccounts[0]
    )
    assert first_account_subaccount_subaccount.created_by == user
    assert first_account_subaccount_subaccount.updated_by == user

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
    compare_subaccounts(
        second_account_subaccount_subaccount,
        child_subaccounts[1]
    )
