from greenbudget.app.account.models import BudgetAccount, TemplateAccount
from greenbudget.app.group.models import (
    BudgetAccountGroup, TemplateAccountGroup)
from greenbudget.app.history.models import (
    Event, FieldAlterationEvent, CreateEvent)


def test_remove_budget_account_from_group_group_deleted(create_budget, user,
        create_budget_account_group):
    budget = create_budget()
    group = create_budget_account_group(parent=budget)
    account = BudgetAccount.objects.create(
        budget=budget,
        identifier="Identifier",
        group=group,
        updated_by=user,
    )
    account.group = None
    account.save()
    assert BudgetAccountGroup.objects.first() is None


def test_remove_template_account_from_group_group_deleted(create_template, user,
        create_template_account_group):
    template = create_template()
    group = create_template_account_group(parent=template)
    account = TemplateAccount.objects.create(
        budget=template,
        identifier="Identifier",
        group=group,
        updated_by=user,
    )
    account.group = None
    account.save()
    assert TemplateAccountGroup.objects.first() is None


def test_remove_budget_account_from_group_group_not_deleted(create_budget,
        create_budget_account, create_budget_account_group):
    budget = create_budget()
    group = create_budget_account_group(parent=budget)
    account = create_budget_account(budget=budget, group=group)
    create_budget_account(budget=budget, group=group)

    account.group = None
    account.save()
    assert BudgetAccountGroup.objects.first() == group


def test_remove_template_account_from_group_group_not_deleted(create_template,
        create_template_account, create_template_account_group):
    template = create_template()
    group = create_template_account_group(parent=template)
    account = create_template_account(budget=template, group=group)
    create_template_account(budget=template, group=group)

    account.group = None
    account.save()
    assert TemplateAccountGroup.objects.first() == group


def test_record_create_history(create_budget, user):
    budget = create_budget()
    account = BudgetAccount.objects.create(
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


def test_record_field_change_history(create_budget, user):
    budget = create_budget()
    account = BudgetAccount(
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


def test_dont_record_field_change_history(create_budget, user):
    budget = create_budget()
    account = BudgetAccount(
        description=None,
        identifier="Identifier",
        budget=budget,
        updated_by=user
    )
    account.save()
    assert FieldAlterationEvent.objects.count() == 0

    account.description = "New Description"
    account.save(track_changes=False)
    assert FieldAlterationEvent.objects.count() == 0


def test_record_field_change_history_null_at_start(create_budget, user):
    budget = create_budget()
    account = BudgetAccount(
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
