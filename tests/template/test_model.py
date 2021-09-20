from greenbudget.app import signals


def test_duplicate_template(user, create_template,
        create_template_account, create_template_subaccount,
        create_fringe, create_template_account_group,
        create_template_subaccount_group):
    with signals.post_save.disable():
        original = create_template(created_by=user)
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
        account_group = create_template_account_group(parent=original)
        accounts = [
            create_template_account(
                budget=original,
                created_by=user,
                updated_by=user,
                group=account_group,
            ),
            create_template_account(
                budget=original,
                created_by=user,
                updated_by=user,
                group=account_group,
            )
        ]
        subaccount_group = create_template_subaccount_group(parent=accounts[0])
        subaccounts = [
            create_template_subaccount(
                parent=accounts[0],
                created_by=user,
                updated_by=user,
                group=subaccount_group
            ),
            create_template_subaccount(
                parent=accounts[1],
                created_by=user,
                updated_by=user
            )
        ]
        child_subaccounts = [
            create_template_subaccount(
                parent=subaccounts[0],
                created_by=user,
                updated_by=user
            ),
            create_template_subaccount(
                parent=subaccounts[1],
                created_by=user,
                updated_by=user
            )
        ]

    template = original.duplicate(user)

    assert template.name == original.name
    assert template.accounts.count() == 2
    assert template.created_by == user

    assert template.groups.count() == 1
    budget_account_group = template.groups.first()
    assert budget_account_group.name == account_group.name
    assert budget_account_group.color == account_group.color

    assert template.fringes.count() == 2

    first_fringe = template.fringes.first()
    assert first_fringe.created_by == user
    assert first_fringe.updated_by == user
    assert first_fringe.name == fringes[0].name
    assert first_fringe.description == fringes[0].description
    assert first_fringe.cutoff == fringes[0].cutoff
    assert first_fringe.rate == fringes[0].rate
    assert first_fringe.unit == fringes[0].unit

    second_fringe = template.fringes.all()[1]
    assert second_fringe.created_by == user
    assert second_fringe.updated_by == user
    assert second_fringe.name == fringes[1].name
    assert second_fringe.description == fringes[1].description
    assert second_fringe.cutoff == fringes[1].cutoff
    assert second_fringe.rate == fringes[1].rate
    assert second_fringe.unit == fringes[1].unit

    assert template.accounts.count() == 2

    first_account = template.accounts.first()
    assert first_account.group == budget_account_group
    assert first_account.identifier == accounts[0].identifier
    assert first_account.description == accounts[0].description
    assert first_account.created_by == user
    assert first_account.updated_by == user

    assert first_account.subaccounts.count() == 1

    assert first_account.groups.count() == 1
    budget_subaccount_group = first_account.groups.first()
    assert budget_subaccount_group.name == subaccount_group.name
    assert budget_subaccount_group.color == subaccount_group.color

    first_account_subaccount = first_account.subaccounts.first()
    assert first_account_subaccount.group == budget_subaccount_group

    assert first_account_subaccount.created_by == user
    assert first_account_subaccount.updated_by == user
    assert first_account_subaccount.identifier == subaccounts[0].identifier
    assert first_account_subaccount.description == subaccounts[0].description
    assert first_account_subaccount.budget == template
    # These values will be None because the subaccount has children.
    assert first_account_subaccount.rate is None
    assert first_account_subaccount.quantity is None
    assert first_account_subaccount.multiplier is None
    assert first_account_subaccount.unit is None

    assert first_account_subaccount.subaccounts.count() == 1
    first_account_subaccount_subaccount = first_account_subaccount.subaccounts.first()  # noqa
    assert first_account_subaccount_subaccount.created_by == user
    assert first_account_subaccount_subaccount.updated_by == user
    assert first_account_subaccount_subaccount.identifier == child_subaccounts[0].identifier  # noqa
    assert first_account_subaccount_subaccount.description == child_subaccounts[0].description  # noqa
    assert first_account_subaccount_subaccount.rate == child_subaccounts[0].rate  # noqa
    assert first_account_subaccount_subaccount.quantity == child_subaccounts[0].quantity  # noqa
    assert first_account_subaccount_subaccount.multiplier == child_subaccounts[0].multiplier  # noqa
    assert first_account_subaccount_subaccount.unit == child_subaccounts[0].unit  # noqa
    assert first_account_subaccount_subaccount.budget == template

    second_account = template.accounts.all()[1]
    assert second_account.group == budget_account_group
    assert second_account.identifier == accounts[1].identifier
    assert second_account.description == accounts[1].description
    assert second_account.created_by == user
    assert second_account.updated_by == user

    assert second_account.subaccounts.count() == 1
    second_account_subaccount = second_account.subaccounts.first()
    assert second_account_subaccount.created_by == user
    assert second_account_subaccount.updated_by == user
    assert second_account_subaccount.identifier == subaccounts[1].identifier
    assert second_account_subaccount.description == subaccounts[1].description
    assert second_account_subaccount.budget == template
    # These values will be None because the subaccount has children.
    assert second_account_subaccount.rate is None
    assert second_account_subaccount.quantity is None
    assert second_account_subaccount.multiplier is None
    assert second_account_subaccount.unit is None

    assert second_account_subaccount.subaccounts.count() == 1
    second_account_subaccount_subaccount = second_account_subaccount.subaccounts.first()  # noqa
    assert second_account_subaccount_subaccount.created_by == user
    assert second_account_subaccount_subaccount.updated_by == user
    assert second_account_subaccount_subaccount.identifier == child_subaccounts[1].identifier  # noqa
    assert second_account_subaccount_subaccount.description == child_subaccounts[1].description  # noqa
    assert second_account_subaccount_subaccount.rate == child_subaccounts[1].rate  # noqa
    assert second_account_subaccount_subaccount.quantity == child_subaccounts[1].quantity  # noqa
    assert second_account_subaccount_subaccount.multiplier == child_subaccounts[1].multiplier  # noqa
    assert second_account_subaccount_subaccount.unit == child_subaccounts[1].unit  # noqa
    assert second_account_subaccount_subaccount.budget == template


def test_derive_budget(user, create_template, create_template_account,
        create_template_subaccount, create_fringe, admin_user,
        create_template_account_group, create_template_subaccount_group):
    with signals.disable([
        signals.post_save,
        signals.post_create_by_user,
        signals.post_create,
        signals.fields_changed,
        signals.field_changed
    ]):
        template = create_template(created_by=admin_user, name="Test Name")
        fringes = [
            create_fringe(
                budget=template,
                created_by=admin_user,
                updated_by=admin_user
            ),
            create_fringe(
                budget=template,
                created_by=admin_user,
                updated_by=admin_user
            ),
        ]
        account_group = create_template_account_group(parent=template)
        accounts = [
            create_template_account(
                budget=template,
                created_by=admin_user,
                updated_by=admin_user,
                group=account_group,
            ),
            create_template_account(
                budget=template,
                created_by=admin_user,
                updated_by=admin_user,
                group=account_group,
            )
        ]
        subaccount_group = create_template_subaccount_group(parent=accounts[0])
        subaccounts = [
            create_template_subaccount(
                parent=accounts[0],
                created_by=admin_user,
                updated_by=admin_user,
                group=subaccount_group
            ),
            create_template_subaccount(
                parent=accounts[1],
                created_by=admin_user,
                updated_by=admin_user
            )
        ]
        child_subaccounts = [
            create_template_subaccount(
                parent=subaccounts[0],
                created_by=admin_user,
                updated_by=admin_user
            ),
            create_template_subaccount(
                parent=subaccounts[1],
                created_by=admin_user,
                updated_by=admin_user
            )
        ]

    budget = template.derive(user)
    budget.refresh_from_db()

    assert budget.name == "Test Name"
    assert budget.accounts.count() == 2
    assert budget.created_by == user

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

    assert budget.accounts.count() == 2

    first_account = budget.accounts.first()
    assert first_account.group == budget_account_group
    assert first_account.identifier == accounts[0].identifier
    assert first_account.description == accounts[0].description
    assert first_account.created_by == user
    assert first_account.updated_by == user

    assert first_account.subaccounts.count() == 1

    assert first_account.groups.count() == 1
    budget_subaccount_group = first_account.groups.first()
    assert budget_subaccount_group.name == subaccount_group.name
    assert budget_subaccount_group.color == subaccount_group.color

    first_account_subaccount = first_account.subaccounts.first()
    assert first_account_subaccount.group == budget_subaccount_group

    assert first_account_subaccount.created_by == user
    assert first_account_subaccount.updated_by == user
    assert first_account_subaccount.identifier == subaccounts[0].identifier
    assert first_account_subaccount.description == subaccounts[0].description
    assert first_account_subaccount.budget == budget
    # These values will be None because the subaccount has children.
    assert first_account_subaccount.rate is None
    assert first_account_subaccount.quantity is None
    assert first_account_subaccount.multiplier is None
    assert first_account_subaccount.unit is None

    assert first_account_subaccount.subaccounts.count() == 1
    first_account_subaccount_subaccount = first_account_subaccount.subaccounts.first()  # noqa
    assert first_account_subaccount_subaccount.created_by == user
    assert first_account_subaccount_subaccount.updated_by == user
    assert first_account_subaccount_subaccount.identifier == child_subaccounts[0].identifier  # noqa
    assert first_account_subaccount_subaccount.description == child_subaccounts[0].description  # noqa
    assert first_account_subaccount_subaccount.rate == child_subaccounts[0].rate  # noqa
    assert first_account_subaccount_subaccount.quantity == child_subaccounts[0].quantity  # noqa
    assert first_account_subaccount_subaccount.multiplier == child_subaccounts[0].multiplier  # noqa
    assert first_account_subaccount_subaccount.unit == child_subaccounts[0].unit  # noqa
    assert first_account_subaccount_subaccount.budget == budget

    second_account = budget.accounts.all()[1]
    assert second_account.group == budget_account_group
    assert second_account.identifier == accounts[1].identifier
    assert second_account.description == accounts[1].description
    assert second_account.created_by == user
    assert second_account.updated_by == user

    assert second_account.subaccounts.count() == 1
    second_account_subaccount = second_account.subaccounts.first()
    assert second_account_subaccount.created_by == user
    assert second_account_subaccount.updated_by == user
    assert second_account_subaccount.identifier == subaccounts[1].identifier
    assert second_account_subaccount.description == subaccounts[1].description
    assert second_account_subaccount.budget == budget
    # These values will be None because the subaccount has children.
    assert second_account_subaccount.rate is None
    assert second_account_subaccount.quantity is None
    assert second_account_subaccount.multiplier is None
    assert second_account_subaccount.unit is None

    assert second_account_subaccount.subaccounts.count() == 1
    second_account_subaccount_subaccount = second_account_subaccount.subaccounts.first()  # noqa
    assert second_account_subaccount_subaccount.created_by == user
    assert second_account_subaccount_subaccount.updated_by == user
    assert second_account_subaccount_subaccount.identifier == child_subaccounts[1].identifier  # noqa
    assert second_account_subaccount_subaccount.description == child_subaccounts[1].description  # noqa
    assert second_account_subaccount_subaccount.rate == child_subaccounts[1].rate  # noqa
    assert second_account_subaccount_subaccount.quantity == child_subaccounts[1].quantity  # noqa
    assert second_account_subaccount_subaccount.multiplier == child_subaccounts[1].multiplier  # noqa
    assert second_account_subaccount_subaccount.unit == child_subaccounts[1].unit  # noqa
    assert second_account_subaccount_subaccount.budget == budget
