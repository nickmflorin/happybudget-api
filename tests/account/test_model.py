from greenbudget.app.account.models import Account
from greenbudget.app.history.models import FieldAlterationEvent


def test_field_changes(create_budget, user):
    budget = create_budget()
    account = Account(
        description="Description",
        identifier="Identifier",
        budget=budget,
        updated_by=user
    )
    account.save()
    assert FieldAlterationEvent.objects.count() == 0

    account.description = "New Description"
    account.save()

    assert FieldAlterationEvent.objects.count() == 1
    alteration = FieldAlterationEvent.objects.first()
    assert alteration.field == "description"
    assert alteration.old_value == "Description"
    assert alteration.new_value == "New Description"


def test_field_changes_null_at_start(create_budget, user):
    budget = create_budget()
    account = Account(
        description=None,
        identifier="Identifier",
        budget=budget,
        updated_by=user
    )
    account.save()
    assert FieldAlterationEvent.objects.count() == 0

    account.description = "Description"
    account.save()

    assert FieldAlterationEvent.objects.count() == 1
    alteration = FieldAlterationEvent.objects.first()
    assert alteration.field == "description"
    assert alteration.old_value is None
    assert alteration.new_value == "Description"
