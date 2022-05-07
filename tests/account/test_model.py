def test_bulk_create_accounts(user, budget_f):
    budget = budget_f.create_budget()
    account_cls = budget_f.budget_cls.account_cls
    instances = [
        account_cls(
            identifier='Account 1',
            parent=budget,
            created_by=user,
            updated_by=user
        ),
        account_cls(
            identifier='Account 2',
            parent=budget,
            created_by=user,
            updated_by=user
        )
    ]
    created = account_cls.objects.bulk_create(instances)

    assert [b.pk for b in created] == [1, 2]
    assert [b.identifier for b in created] == ["Account 1", "Account 2"]
    assert all([b.budget == budget] for b in created)

    assert account_cls.objects.count() == 2

    accounts = account_cls.objects.all()
    assert [b.identifier for b in accounts] == ["Account 1", "Account 2"]
    assert all([b.budget == budget] for b in accounts)
