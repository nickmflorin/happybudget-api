from greenbudget.app.account.models import Account
from greenbudget.app.history.models import (
    Event, FieldAlterationEvent, CreateEvent)


def test_create_history(create_budget, user):
    budget = create_budget()
    account = Account.objects.create(
        description="Description",
        identifier="Identifier",
        budget=budget,
        updated_by=user
    )
    assert Event.objects.count() == 1
    event = Event.objects.first()
    assert isinstance(event, CreateEvent)
    assert event.user == user
    assert event.content_object == account


def test_field_change_history(create_budget, user):
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
    assert alteration.user == user
    assert alteration.field == "description"
    assert alteration.old_value == "Description"
    assert alteration.new_value == "New Description"


def test_field_change_history_null_at_start(create_budget, user):
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
    assert alteration.user == user
