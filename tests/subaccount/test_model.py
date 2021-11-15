from django.contrib.contenttypes.models import ContentType


def test_bulk_create_subaccounts(user, budget_f, models):
    budget = budget_f.create_budget()
    accounts = [
        budget_f.create_account(parent=budget),
        budget_f.create_account(parent=budget)
    ]
    subaccounts = [
        budget_f.subaccount_cls(
            content_type=ContentType.objects.get_for_model(budget_f.account_cls),
            object_id=accounts[0].pk,
            identifier="Sub Account 1",
            created_by=user,
            updated_by=user
        ),
        budget_f.subaccount_cls(
            content_type=ContentType.objects.get_for_model(budget_f.account_cls),
            object_id=accounts[0].pk,
            identifier="Sub Account 2",
            created_by=user,
            updated_by=user
        ),
        budget_f.subaccount_cls(
            content_type=ContentType.objects.get_for_model(budget_f.account_cls),
            object_id=accounts[1].pk,
            identifier="Sub Account 3",
            created_by=user,
            updated_by=user
        )
    ]
    created_subaccounts = budget_f.subaccount_cls.objects.bulk_create(
        subaccounts,
        return_created_objects=True
    )

    assert [b.pk for b in created_subaccounts] == [1, 2, 3]
    assert [b.identifier for b in created_subaccounts] == [
        "Sub Account 1", "Sub Account 2", "Sub Account 3"]
    assert all([b.budget == budget] for b in created_subaccounts)
    assert created_subaccounts[0].parent == accounts[0]
    assert created_subaccounts[1].parent == accounts[0]
    assert created_subaccounts[2].parent == accounts[1]

    assert models.SubAccount.objects.count() == 3
    assert budget_f.subaccount_cls.objects.count() == 3

    subaccounts = budget_f.subaccount_cls.objects.all()
    assert [b.identifier for b in subaccounts] == [
        "Sub Account 1", "Sub Account 2", "Sub Account 3"]
    assert all([b.budget == budget] for b in accounts)
