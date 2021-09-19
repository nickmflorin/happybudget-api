def test_bulk_create_accounts(models, create_budget, user):
    budget = create_budget()
    instances = [
        models.BudgetAccount(
            identifier='Account 1',
            parent=budget,
            created_by=user,
            updated_by=user
        ),
        models.BudgetAccount(
            identifier='Account 2',
            parent=budget,
            created_by=user,
            updated_by=user
        )
    ]
    created = models.BudgetAccount.objects.bulk_create(instances,
        return_created_objects=True)
    assert [b.pk for b in created] == [1, 2]
    assert [b.identifier for b in created] == ["Account 1", "Account 2"]
    assert all([b.budget == budget] for b in created)

    assert models.Account.objects.count() == 2
    assert models.BudgetAccount.objects.count() == 2

    accounts = models.BudgetAccount.objects.all()
    assert [b.identifier for b in accounts] == ["Account 1", "Account 2"]
    assert all([b.budget == budget] for b in accounts)
