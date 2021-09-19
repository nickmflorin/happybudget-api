import datetime
from datetime import timezone
import pytest
from django.test import override_settings

from greenbudget.app import signals


@pytest.mark.freeze_time
def test_saving_subaccount_saves_budget(create_budget, create_budget_account,
        freezer):
    freezer.move_to('2017-05-20')
    with signals.post_save.disable():
        budget = create_budget()
        account = create_budget_account(parent=budget)
        freezer.move_to('2019-05-20')
    account.save()
    budget.refresh_from_db()
    assert budget.updated_at == datetime.datetime(
        2019, 5, 20).replace(tzinfo=timezone.utc)


@override_settings(TRACK_MODEL_HISTORY=True)
def test_record_create_history(create_budget, user, models):
    budget = create_budget()
    account = models.BudgetAccount.objects.create(
        description="Description",
        identifier="Identifier",
        parent=budget,
        updated_by=user,
        created_by=user
    )
    assert models.Event.objects.count() == 1
    event = models.Event.objects.first()
    assert isinstance(event, models.CreateEvent)
    assert event.user == user
    assert event.content_object == account


@override_settings(TRACK_MODEL_HISTORY=True)
def test_record_field_change_history(create_budget, user, models):
    budget = create_budget()
    account = models.BudgetAccount(
        description="Description",
        identifier="Identifier",
        parent=budget,
        updated_by=user,
        created_by=user
    )
    account.save()
    assert models.FieldAlterationEvent.objects.count() == 0

    account.description = "New Description"
    account.save()

    assert models.FieldAlterationEvent.objects.count() == 1
    alteration = models.FieldAlterationEvent.objects.first()
    assert alteration.user == user
    assert alteration.field == "description"
    assert alteration.old_value == "Description"
    assert alteration.new_value == "New Description"


@override_settings(TRACK_MODEL_HISTORY=True)
def test_dont_record_field_change_history(create_budget, user, models):
    budget = create_budget()
    account = models.BudgetAccount(
        description=None,
        identifier="Identifier",
        parent=budget,
        updated_by=user,
        created_by=user
    )
    account.save()
    assert models.FieldAlterationEvent.objects.count() == 0

    account.description = "New Description"
    account.save(track_changes=False)
    assert models.FieldAlterationEvent.objects.count() == 0


@override_settings(TRACK_MODEL_HISTORY=True)
def test_record_field_change_history_null_at_start(create_budget, user, models):
    budget = create_budget()
    account = models.BudgetAccount(
        description=None,
        identifier="Identifier",
        parent=budget,
        updated_by=user,
        created_by=user
    )
    account.save()
    assert models.FieldAlterationEvent.objects.count() == 0

    account.description = "Description"
    account.save()

    assert models.FieldAlterationEvent.objects.count() == 1
    alteration = models.FieldAlterationEvent.objects.first()
    assert alteration.field == "description"
    assert alteration.old_value is None
    assert alteration.new_value == "Description"
    assert alteration.user == user
