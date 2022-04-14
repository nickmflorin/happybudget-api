def test_bulk_create_budgets(models, user):
    instances = [
        models.Budget(name='Budget 1', created_by=user, updated_by=user),
        models.Budget(name='Budget 2', created_by=user, updated_by=user)
    ]
    created = models.Budget.objects.bulk_create(instances,
        return_created_objects=True)
    assert [b.pk for b in created] == [1, 2]
    assert [b.name for b in created] == ["Budget 1", "Budget 2"]
    assert [b.created_by for b in created] == [user, user]
    assert [b.updated_by for b in created] == [user, user]

    assert models.Budget.objects.count() == 2
    assert models.BaseBudget.objects.count() == 2

    budgets = models.Budget.objects.all()
    assert [b.name for b in budgets] == ["Budget 2", "Budget 1"]
    assert all([b.created_by == user] for b in budgets)
    assert all([b.updated_by == user] for b in budgets)
