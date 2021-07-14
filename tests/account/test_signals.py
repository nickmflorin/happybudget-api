import datetime
from datetime import timezone
import pytest
from django.test import override_settings

from greenbudget.app import signals


def test_remove_budget_account_from_group_group_deleted(create_budget, user,
        create_budget_account_group, models):
    budget = create_budget()
    group = create_budget_account_group(parent=budget)
    account = models.BudgetAccount.objects.create(
        budget=budget,
        identifier="Identifier",
        group=group,
        updated_by=user,
        created_by=user
    )
    account.group = None
    account.save()
    assert models.BudgetAccountGroup.objects.first() is None


@pytest.mark.freeze_time
def test_saving_subaccount_saves_budget(create_budget, create_budget_account,
        freezer):
    freezer.move_to('2017-05-20')
    with signals.post_save.disable():
        budget = create_budget()
        account = create_budget_account(budget=budget)
        freezer.move_to('2019-05-20')
    account.save()
    budget.refresh_from_db()
    assert budget.updated_at == datetime.datetime(
        2019, 5, 20).replace(tzinfo=timezone.utc)


def test_remove_template_account_from_group_group_deleted(create_template, user,
        create_template_account_group, models):
    template = create_template()
    group = create_template_account_group(parent=template)
    account = models.TemplateAccount.objects.create(
        budget=template,
        identifier="Identifier",
        group=group,
        updated_by=user,
        created_by=user
    )
    account.group = None
    account.save()
    assert models.TemplateAccountGroup.objects.first() is None


def test_remove_budget_account_from_group_group_not_deleted(create_budget,
        create_budget_account, create_budget_account_group, models):
    budget = create_budget()
    group = create_budget_account_group(parent=budget)
    account = create_budget_account(budget=budget, group=group)
    create_budget_account(budget=budget, group=group)

    account.group = None
    account.save()
    assert models.BudgetAccountGroup.objects.first() == group


def test_remove_template_account_from_group_group_not_deleted(create_template,
        create_template_account, create_template_account_group, models):
    template = create_template()
    group = create_template_account_group(parent=template)
    account = create_template_account(budget=template, group=group)
    create_template_account(budget=template, group=group)

    account.group = None
    account.save()
    assert models.TemplateAccountGroup.objects.first() == group


@override_settings(TRACK_MODEL_HISTORY=True)
def test_record_create_history(create_budget, user, models):
    budget = create_budget()
    account = models.BudgetAccount.objects.create(
        description="Description",
        identifier="Identifier",
        budget=budget,
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
        budget=budget,
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
        budget=budget,
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
        budget=budget,
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
