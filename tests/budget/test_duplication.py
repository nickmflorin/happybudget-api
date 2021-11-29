import pytest


@pytest.fixture
def generate_data(create_fringe, create_group, create_markup):
    def generate(factory, user):
        template = factory.create_budget(created_by=user, name="Test Name")
        original_fringes = [
            create_fringe(
                budget=template,
                created_by=user,
                updated_by=user
            ),
            create_fringe(
                budget=template,
                created_by=user,
                updated_by=user
            ),
        ]
        original_account_groups = [
            create_group(parent=template),
            create_group(parent=template),
            create_group(parent=template)
        ]
        original_account_markups = [
            create_markup(parent=template),
            create_markup(parent=template),
            create_markup(parent=template)
        ]
        # Determines how Markup's should be allocated amongst each individual
        # account.
        markup_designation = [(0, 1), None, (0, 1, 2), None, (0, 1, 2), (2, )]
        # Determines how Group's should be allocated amonst each invididual
        # account.
        group_designation = [0, 0, None, 1, 1, 2]

        original_accounts = []
        for i in range(6):
            m_designation = markup_designation[i] or []
            g_designation = group_designation[i]
            group = None
            if g_designation is not None:
                group = original_account_groups[g_designation]
            original_accounts.append(factory.create_account(
                parent=template,
                created_by=user,
                updated_by=user,
                group=group,
                markups=[original_account_markups[j] for j in m_designation]
            ))

        original_subaccount_groups = {}
        original_child_subaccount_groups = {}
        original_subaccounts = {}
        original_child_subaccounts = {}

        for account in original_accounts:
            # Create 2 SubAccount(s) for each Account, each with it's own Group.
            original_subaccount_groups[account.pk] = [
                create_group(parent=account),
                create_group(parent=account),
            ]
            new_subaccounts = []
            for i in range(2):
                new_subaccounts.append(factory.create_subaccount(
                    parent=account,
                    created_by=user,
                    updated_by=user,
                    fringes=[original_fringes[i]],
                    group=original_subaccount_groups[account.pk][i]
                ))
            original_subaccounts[account.pk] = new_subaccounts
            # Create 2 SubAccount(s) for each SubAccount, each with it's own
            # Group.
            for subaccount in new_subaccounts:
                original_child_subaccounts[subaccount.pk] = []
                original_child_subaccount_groups[subaccount.pk] = [
                    create_group(parent=subaccount),
                    create_group(parent=subaccount),
                ]
                for i in range(2):
                    original_child_subaccounts[subaccount.pk].append(
                        factory.create_subaccount(
                            parent=subaccount,
                            created_by=user,
                            updated_by=user,
                            fringes=[original_fringes[i]],
                            group=original_child_subaccount_groups[subaccount.pk][i]  # noqa
                        ))

        return {
            'base': template,
            'fringes': original_fringes,
            'account_groups': original_account_groups,
            'accounts': original_accounts,
            'subaccounts': original_subaccounts,
            'subaccount_groups': original_subaccount_groups,
            'child_subaccounts': original_child_subaccounts
        }
    return generate


@pytest.fixture
def make_assertions():
    def make_assert(data, base, user):
        assert base.name == "Test Name"
        assert base.children.count() == len(data['accounts'])
        assert base.created_by == user
        assert base.groups.count() == len(data['account_groups'])
        assert base.fringes.count() == len(data['fringes'])

        def assert_model(original, derived, fields):
            model_name = original.__class__.__name__
            derived_model_name = derived.__class__.__name__

            for field in fields:
                assert getattr(original, field) == getattr(derived, field), \
                    "The original %s has a value of %s for field %s, whereas " \
                    "the derived %s has a value of %s." % (
                        model_name, getattr(original, field), field,
                        derived_model_name, getattr(derived, field)
                )

            # The `created_by` field on the model (if applicable) should be
            # updated to the user that perform the derivation.
            if hasattr(derived, "created_by"):
                assert derived.created_by == user, \
                    "The created_by field wasn't properly changed for the " \
                    "derived model %s." % derived.__class__.__name__
            # The `updated_by` field on the model (if applicable) should be
            # updated to the user that perform the derivation.
            if hasattr(derived, "updated_by"):
                assert derived.updated_by == user, \
                    "The updated_by field wasn't properly changed for the " \
                    "derived model %s." % derived.__class__.__name__

        def get_name(data):
            if isinstance(data, (list, tuple)):
                if len(data) != 0:
                    return data[0].__class__.__name__
                return "Unknown"
            return data.model.__name__

        def get_count(data):
            if isinstance(data, (list, tuple)):
                return len(data)
            return data.count()

        def get_at_index(data, index):
            if isinstance(data, (list, tuple)):
                return data[index]
            return data.all()[index]

        def assert_count(original_models, new_models):
            original_name = get_name(original_models)
            derived_model_name = get_name(new_models)

            assert get_count(new_models) == get_count(original_models), \
                "The number of %s(s) is %s while the number of derived %s(s) " \
                "is %s... they should be equal." % (
                    original_name, get_count(
                        original_models), derived_model_name,
                    get_count(new_models))

        def assert_models(original_models, new_models, fields=None,
                asserter=None):
            assert_count(original_models, new_models)

            for i in range(get_count(original_models)):
                original = get_at_index(original_models, i)
                derived = get_at_index(new_models, i)
                if asserter is not None:
                    asserter(original, derived)
                else:
                    assert_model(original, derived, fields)

        def assert_group(original, derived):
            assert_model(original, derived, ["name", "color"])

        def assert_groups(original, derived):
            assert_models(original, derived, asserter=assert_group)

        def assert_fringe(original, derived):
            assert_model(original, derived, [
                "name", "description", "rate", "cutoff", "unit"])

        def assert_fringes(original, derived):
            assert_models(original, derived, asserter=assert_fringe)

        def assert_markup(original, derived):
            assert_model(original, derived, [
                "identifier", "description", "rate", "unit"])

        def assert_markups(original, derived):
            assert_models(original, derived, asserter=assert_markup)

        def assert_account(original, derived):
            assert_model(original, derived, ["identifier", "description"])
            if original.group is None:
                assert derived.group is None
            else:
                assert derived.group is not None
                assert_group(original.group, derived.group)

            assert_markups(original.markups, derived.markups)

        def assert_subaccount(original, derived, parent):
            assert_model(original, derived, [
                "identifier", "description", "rate", "quantity", "multiplier",
                "unit"])
            assert derived.parent == parent
            if original.group is None:
                assert derived.group is None
            else:
                assert derived.group is not None
                assert_group(original.group, derived.group)

            assert_markups(original.markups, derived.markups)
            assert_fringes(original.fringes, derived.fringes)

        assert_groups(data['account_groups'], base.groups)
        assert_fringes(data['fringes'], base.fringes)

        for i, account in enumerate(base.children.all()):
            original_account = data['accounts'][i]
            assert_account(original_account, account)

            original_subs = data['subaccounts'][original_account.pk]
            assert account.children.count() == len(original_subs)

            for j, subaccount in enumerate(account.children.all()):
                original_subaccount = original_subs[j]
                assert_subaccount(original_subaccount,
                                  subaccount, parent=account)

                original_child_subs = data['child_subaccounts'][original_subaccount.pk]  # noqa
                assert subaccount.children.count() == len(original_child_subs)

                for k, child_subaccount in enumerate(subaccount.children.all()):
                    original_child_subaccount = original_child_subs[k]
                    assert_subaccount(
                        original=original_child_subaccount,
                        derived=child_subaccount,
                        parent=subaccount
                    )
    return make_assert


def test_duplicate_budget(budget_df, user, generate_data, make_assertions,
        models):
    # TODO: Incorporate actuals into the test.
    data = generate_data(budget_df, user)
    budget = models.Budget.objects.duplicate(data['base'], user)
    assert isinstance(budget, models.Budget)
    make_assertions(data, budget, user)


def test_duplicate_template(template_df, user, generate_data, make_assertions,
        models):
    data = generate_data(template_df, user)
    template = models.Template.objects.duplicate(data['base'], user)
    assert isinstance(template, models.Template)
    make_assertions(data, template, user)


def test_derive_budget(template_df, user, generate_data, make_assertions,
        models, admin_user):
    data = generate_data(template_df, admin_user)
    budget = models.Template.objects.derive(data['base'], user)
    budget.refresh_from_db()
    make_assertions(data, budget, user)
