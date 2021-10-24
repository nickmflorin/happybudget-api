import datetime
from datetime import timezone
import pytest
from django.test import override_settings

from greenbudget.app import signals


@pytest.mark.parametrize('context', ['budget', 'template'])
def test_delete_account_reestimates(create_context_budget, create_account,
        create_subaccount, context):
    budget = create_context_budget(context=context)
    account = create_account(parent=budget, context=context)
    parent_subaccount = create_subaccount(parent=account, context=context)
    subaccount = create_subaccount(
        parent=parent_subaccount,
        context=context,
        rate=1,
        multiplier=5,
        quantity=10,
    )
    assert parent_subaccount.nominal_value == 50.0
    assert subaccount.nominal_value == 50.0
    assert account.nominal_value == 50.0
    assert budget.nominal_value == 50.0

    account.delete()
    assert budget.nominal_value == 0.0


def test_delete_account_reactualizes(create_budget, create_budget_account,
        create_budget_subaccount, create_actual):
    budget = create_budget()
    account = create_budget_account(parent=budget)
    parent_subaccount = create_budget_subaccount(parent=account)
    subaccount = create_budget_subaccount(
        parent=parent_subaccount,
        rate=1,
        multiplier=5,
        quantity=10,
    )
    create_actual(owner=subaccount, budget=budget, value=100.0)

    assert budget.actual == 100.0
    assert account.actual == 100.0
    assert parent_subaccount.actual == 100.0
    assert subaccount.actual == 100.0

    account.delete()

    assert budget.actual == 0.0


@pytest.mark.freeze_time
@pytest.mark.parametrize('context', ['budget', 'template'])
def test_saving_subaccount_saves_budget(create_context_budget, create_account,
        freezer, context):
    freezer.move_to('2017-05-20')
    with signals.post_save.disable():
        budget = create_context_budget(context=context)
        account = create_account(parent=budget, context=context)
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
