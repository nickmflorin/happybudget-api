import datetime
from datetime import timezone
import pytest

from django.contrib.contenttypes.models import ContentType
from django.test import override_settings

from greenbudget.app import signals


def test_delete_subaccount_recalculates(create_budget,
        create_budget_account, create_budget_subaccount):
    budget = create_budget()
    account = create_budget_account(parent=budget)
    parent_subaccount = create_budget_subaccount(parent=account)
    subaccount = create_budget_subaccount(
        parent=parent_subaccount,
        rate=1,
        multiplier=5,
        quantity=10,
    )
    assert parent_subaccount.nominal_value == 50.0
    assert subaccount.nominal_value == 50.0
    assert account.nominal_value == 50.0
    assert budget.nominal_value == 50.0

    subaccount.delete()
    assert account.nominal_value == 0.0
    assert budget.nominal_value == 0.0
    assert parent_subaccount.nominal_value == 0.0


def test_create_subaccount_recalculates(create_budget, create_budget_account,
        create_budget_subaccount):
    budget = create_budget()
    account = create_budget_account(parent=budget)
    subaccount = create_budget_subaccount(
        parent=account,
        rate=1,
        multiplier=5,
        quantity=10,
    )
    assert subaccount.nominal_value == 50.0
    assert account.nominal_value == 50.0
    assert budget.nominal_value == 50.0


def test_update_subaccount_recalculates(create_budget, create_budget_account,
        create_budget_subaccount):
    budget = create_budget()
    account = create_budget_account(parent=budget)
    subaccount = create_budget_subaccount(
        parent=account,
        rate=1,
        multiplier=5,
        quantity=10,
    )
    assert subaccount.nominal_value == 50.0
    assert account.nominal_value == 50.0
    assert budget.nominal_value == 50.0

    subaccount.quantity = 1
    subaccount.save(update_fields=['quantity'])
    assert subaccount.nominal_value == 5.0
    assert account.nominal_value == 5.0
    assert budget.nominal_value == 5.0


def test_change_subaccount_parent_recalculates(models, create_budget,
        create_budget_account, create_budget_subaccount):
    budget = create_budget()
    account = create_budget_account(parent=budget)
    another_account = create_budget_account(parent=budget)
    subaccount = create_budget_subaccount(
        parent=account,
        rate=1,
        multiplier=5,
        quantity=10,
    )
    assert subaccount.nominal_value == 50.0
    assert account.nominal_value == 50.0
    assert budget.nominal_value == 50.0
    assert another_account.nominal_value == 0.0

    subaccount.content_type = ContentType.objects.get_for_model(
        models.BudgetAccount)
    subaccount.object_id = another_account.pk
    subaccount.save(update_fields=['content_type', 'object_id'])

    assert subaccount.nominal_value == 50.0
    another_account.refresh_from_db()
    assert another_account.nominal_value == 50.0
    account.refresh_from_db()
    assert account.nominal_value == 0.0
    assert budget.nominal_value == 50.0


@pytest.mark.freeze_time
def test_saving_subaccount_saves_budget(create_budget, create_budget_account,
        create_budget_subaccount, freezer):
    freezer.move_to('2017-05-20')
    budget = create_budget()
    account = create_budget_account(parent=budget)
    subaccount = create_budget_subaccount(parent=account)
    freezer.move_to('2019-05-20')
    subaccount.save()
    budget.refresh_from_db()
    assert budget.updated_at == datetime.datetime(
        2019, 5, 20).replace(tzinfo=timezone.utc)


@override_settings(TRACK_MODEL_HISTORY=True)
def test_record_create_history(create_budget, create_budget_account, user,
        models):
    with signals.post_create_by_user.disable():
        budget = create_budget()
        account = create_budget_account(parent=budget)
    subaccount = models.BudgetSubAccount.objects.create(
        description="Description",
        identifier="Identifier",
        updated_by=user,
        parent=account,
        created_by=user,
    )
    assert models.Event.objects.count() == 1
    event = models.Event.objects.first()
    assert isinstance(event, models.CreateEvent)
    assert event.user == user
    assert event.content_object == subaccount


@override_settings(TRACK_MODEL_HISTORY=True)
def test_record_field_change_history(create_budget, create_budget_account,
        user, models):
    budget = create_budget()
    account = create_budget_account(parent=budget)
    subaccount = models.BudgetSubAccount(
        description="Description",
        identifier="Identifier",
        parent=account,
        updated_by=user,
        created_by=user
    )
    subaccount.save()
    assert models.FieldAlterationEvent.objects.count() == 0

    subaccount.description = "New Description"
    subaccount.save()

    assert models.FieldAlterationEvent.objects.count() == 1
    alteration = models.FieldAlterationEvent.objects.first()
    assert alteration.user == user
    assert alteration.field == "description"
    assert alteration.old_value == "Description"
    assert alteration.new_value == "New Description"


@override_settings(TRACK_MODEL_HISTORY=True)
def test_dont_record_field_change_history(create_budget, create_budget_account,
        user, models):
    budget = create_budget()
    account = create_budget_account(parent=budget)
    subaccount = models.BudgetSubAccount(
        description="Description",
        identifier="Identifier",
        parent=account,
        updated_by=user,
        created_by=user
    )
    subaccount.save()
    assert models.FieldAlterationEvent.objects.count() == 0

    subaccount.description = "New Description"
    subaccount.save(track_changes=False)
    assert models.FieldAlterationEvent.objects.count() == 0


@override_settings(TRACK_MODEL_HISTORY=True)
def test_record_field_change_history_null_at_start(create_budget, models,
        create_budget_account, user):
    budget = create_budget()
    account = create_budget_account(parent=budget)
    subaccount = models.BudgetSubAccount(
        description=None,
        identifier="Identifier",
        updated_by=user,
        parent=account,
        created_by=user
    )
    subaccount.save()
    assert models.FieldAlterationEvent.objects.count() == 0

    subaccount.description = "Description"
    subaccount.save()

    assert models.FieldAlterationEvent.objects.count() == 1
    alteration = models.FieldAlterationEvent.objects.first()
    assert alteration.field == "description"
    assert alteration.old_value is None
    assert alteration.new_value == "Description"
    assert alteration.user == user
