import datetime
from datetime import timezone
from django.db import IntegrityError
import pytest


def test_budget_group_parent_constraint(create_budget_subaccount,
        create_budget_account, create_budget, create_budget_subaccount_group):
    budget = create_budget()
    account = create_budget_account(budget=budget)
    another_account = create_budget_account(budget=budget)
    group = create_budget_subaccount_group(parent=account)
    with pytest.raises(IntegrityError):
        create_budget_subaccount(
            parent=another_account,
            budget=budget,
            group=group
        )


def test_fringes_constraint(create_budget_subaccount, create_budget_account,
        create_budget, create_fringe):
    budget = create_budget()
    another_budget = create_budget()
    account = create_budget_account(budget=budget)
    subaccount = create_budget_subaccount(budget=budget, parent=account)
    fringe = create_fringe(budget=another_budget)
    subaccount.fringes.add(fringe)
    with pytest.raises(IntegrityError):
        subaccount.save()


def test_template_group_parent_constraint(create_budget_subaccount,
        create_budget_account, create_budget, create_budget_subaccount_group):
    budget = create_budget()
    account = create_budget_account(budget=budget)
    another_account = create_budget_account(budget=budget)
    group = create_budget_subaccount_group(parent=account)
    with pytest.raises(IntegrityError):
        create_budget_subaccount(
            parent=another_account,
            budget=budget,
            group=group
        )


@pytest.mark.freeze_time
def test_saving_subaccount_saves_budget(create_budget, create_budget_account,
        create_budget_subaccount, freezer):
    freezer.move_to('2017-05-20')
    budget = create_budget()
    account = create_budget_account(budget=budget)
    subaccount = create_budget_subaccount(parent=account, budget=budget)
    freezer.move_to('2019-05-20')
    subaccount.save()
    budget.refresh_from_db()
    assert budget.updated_at == datetime.datetime(
        2019, 5, 20).replace(tzinfo=timezone.utc)


def test_remove_budget_subaccount_from_group_group_deleted(user, create_budget,
        create_budget_account, create_budget_subaccount_group, models):
    budget = create_budget()
    account = create_budget_account(budget=budget)
    group = create_budget_subaccount_group(parent=account)
    subaccount = models.BudgetSubAccount.objects.create(
        budget=budget,
        parent=account,
        identifier="Identifier",
        group=group,
        updated_by=user,
    )
    subaccount.group = None
    subaccount.save()
    assert models.BudgetSubAccountGroup.objects.first() is None


def test_remove_template_subaccount_from_group_group_deleted(user, models,
        create_template, create_template_account,
        create_template_subaccount_group):
    template = create_template()
    account = create_template_account(budget=template)
    group = create_template_subaccount_group(parent=account)
    subaccount = models.TemplateSubAccount.objects.create(
        budget=template,
        parent=account,
        identifier="Identifier",
        group=group,
        updated_by=user,
    )
    subaccount.group = None
    subaccount.save()
    assert models.TemplateSubAccountGroup.objects.first() is None


def test_remove_budget_subaccount_from_group_group_not_deleted(create_budget,
        create_budget_subaccount, create_budget_account, models,
        create_budget_subaccount_group):
    budget = create_budget()
    account = create_budget_account(budget=budget)
    group = create_budget_subaccount_group(parent=account)
    subaccount = create_budget_subaccount(
        budget=budget,
        parent=account,
        group=group
    )
    create_budget_subaccount(budget=budget, parent=account, group=group)
    subaccount.group = None
    subaccount.save()
    assert models.BudgetSubAccountGroup.objects.first() == group


def test_remove_template_subaccount_from_group_group_not_deleted(models,
        create_template, create_template_subaccount, create_template_account,
        create_template_subaccount_group):
    budget = create_template()
    account = create_template_account(budget=budget)
    group = create_template_subaccount_group(parent=account)
    subaccount = create_template_subaccount(
        budget=budget,
        parent=account,
        group=group
    )
    create_template_subaccount(budget=budget, parent=account, group=group)
    subaccount.group = None
    subaccount.save()
    assert models.TemplateSubAccountGroup.objects.first() == group


def test_record_create_history(create_budget, create_budget_account, user,
        models):
    budget = create_budget()
    account = create_budget_account(budget=budget)
    subaccount = models.BudgetSubAccount.objects.create(
        description="Description",
        identifier="Identifier",
        budget=budget,
        updated_by=user,
        parent=account
    )
    assert models.Event.objects.count() == 1
    event = models.Event.objects.first()
    assert isinstance(event, models.CreateEvent)
    assert event.user == user
    assert event.content_object == subaccount


def test_record_field_change_history(create_budget, create_budget_account,
        user, models):
    budget = create_budget()
    account = create_budget_account(budget=budget)
    subaccount = models.BudgetSubAccount(
        description="Description",
        identifier="Identifier",
        budget=budget,
        parent=account,
        updated_by=user
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


def test_dont_record_field_change_history(create_budget, create_budget_account,
        user, models):
    budget = create_budget()
    account = create_budget_account(budget=budget)
    subaccount = models.BudgetSubAccount(
        description="Description",
        identifier="Identifier",
        budget=budget,
        parent=account,
        updated_by=user
    )
    subaccount.save()
    assert models.FieldAlterationEvent.objects.count() == 0

    subaccount.description = "New Description"
    subaccount.save(track_changes=False)
    assert models.FieldAlterationEvent.objects.count() == 0


def test_record_field_change_history_null_at_start(create_budget, models,
        create_budget_account, user):
    budget = create_budget()
    account = create_budget_account(budget=budget)
    subaccount = models.BudgetSubAccount(
        description=None,
        identifier="Identifier",
        budget=budget,
        updated_by=user,
        parent=account,
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
