from django.db import IntegrityError
import pytest

from greenbudget.app.subaccount.models import SubAccount, SubAccountGroup
from greenbudget.app.history.models import (
    Event, FieldAlterationEvent, CreateEvent)


@pytest.mark.freeze_time('2020-01-01')
def test_group_parent_constraint(create_sub_account, create_account,
        create_budget, create_sub_account_group):
    budget = create_budget()
    account = create_account(budget=budget)
    another_account = create_account(budget=budget)
    group = create_sub_account_group(parent=account)
    with pytest.raises(IntegrityError):
        create_sub_account(
            parent=another_account,
            budget=budget,
            group=group
        )


def test_remove_from_group_group_deleted(create_account, create_budget,
        create_sub_account_group, user):
    budget = create_budget()
    account = create_account(budget=budget)
    group = create_sub_account_group(parent=account)

    subaccount = SubAccount.objects.create(
        budget=budget,
        parent=account,
        identifier="Identifier",
        group=group,
        updated_by=user,
    )

    subaccount.group = None
    subaccount.save()

    assert SubAccountGroup.objects.first() is None


def test_remove_from_group_group_not_deleted(create_sub_account, create_account,
        create_budget, create_sub_account_group):
    budget = create_budget()
    account = create_account(budget=budget)
    group = create_sub_account_group(parent=account)
    subaccount = create_sub_account(budget=budget, parent=account, group=group)
    create_sub_account(budget=budget, parent=account, group=group)

    subaccount.group = None
    subaccount.save()

    assert SubAccountGroup.objects.first() == group


def test_record_create_history(create_budget, create_account, user):
    budget = create_budget()
    account = create_account(budget=budget)
    subaccount = SubAccount.objects.create(
        description="Description",
        identifier="Identifier",
        budget=budget,
        updated_by=user,
        parent=account
    )
    assert Event.objects.count() == 1
    event = Event.objects.first()
    assert isinstance(event, CreateEvent)
    assert event.user == user
    assert event.content_object == subaccount


def test_record_field_change_history(create_budget, create_account, user):
    budget = create_budget()
    account = create_account(budget=budget)
    subaccount = SubAccount(
        description="Description",
        identifier="Identifier",
        budget=budget,
        parent=account,
        updated_by=user
    )
    subaccount.save()
    assert FieldAlterationEvent.objects.count() == 0

    subaccount.description = "New Description"
    subaccount.save()

    assert FieldAlterationEvent.objects.count() == 1
    alteration = FieldAlterationEvent.objects.first()
    assert alteration.user == user
    assert alteration.field == "description"
    assert alteration.old_value == "Description"
    assert alteration.new_value == "New Description"


def test_dont_record_field_change_history(create_budget, create_account, user):
    budget = create_budget()
    account = create_account(budget=budget)
    subaccount = SubAccount(
        description="Description",
        identifier="Identifier",
        budget=budget,
        parent=account,
        updated_by=user
    )
    subaccount.save()
    assert FieldAlterationEvent.objects.count() == 0

    subaccount.description = "New Description"
    subaccount.save(track_changes=False)
    assert FieldAlterationEvent.objects.count() == 0


def test_record_field_change_history_null_at_start(create_budget,
        create_account, user):
    budget = create_budget()
    account = create_account(budget=budget)
    subaccount = SubAccount(
        description=None,
        identifier="Identifier",
        budget=budget,
        updated_by=user,
        parent=account,
    )
    subaccount.save()
    assert FieldAlterationEvent.objects.count() == 0

    subaccount.description = "Description"
    subaccount.save()

    assert FieldAlterationEvent.objects.count() == 1
    alteration = FieldAlterationEvent.objects.first()
    assert alteration.field == "description"
    assert alteration.old_value is None
    assert alteration.new_value == "Description"
    assert alteration.user == user
