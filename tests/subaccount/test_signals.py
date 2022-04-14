import datetime
from datetime import timezone
import pytest

from django.contrib.contenttypes.models import ContentType


@pytest.mark.freeze_time
def test_delete_subaccount_reestimates(budget_f, freezer):
    freezer.move_to('2017-05-20')
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    parent_subaccount = budget_f.create_subaccount(parent=account)
    subaccount = budget_f.create_subaccount(
        parent=parent_subaccount,
        rate=1,
        multiplier=5,
        quantity=10
    )
    assert parent_subaccount.nominal_value == 50.0
    assert subaccount.nominal_value == 50.0
    assert account.nominal_value == 50.0
    assert budget.nominal_value == 50.0

    freezer.move_to('2019-05-20')

    subaccount.delete()

    assert account.nominal_value == 0.0
    assert budget.nominal_value == 0.0
    assert parent_subaccount.nominal_value == 0.0
    assert budget.updated_at == datetime.datetime(
        2019, 5, 20).replace(tzinfo=timezone.utc)


def test_delete_subaccount_reactualizes(create_budget,
        create_budget_account, create_budget_subaccount, create_actual):
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

    subaccount.delete()
    assert budget.actual == 0.0
    assert account.actual == 0.0
    assert parent_subaccount.actual == 0.0


def test_create_subaccount_rereestimates(budget_f):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    subaccount = budget_f.create_subaccount(
        parent=account,
        rate=1,
        multiplier=5,
        quantity=10,
    )
    assert subaccount.nominal_value == 50.0
    assert account.nominal_value == 50.0
    assert budget.nominal_value == 50.0


def test_update_subaccount_rereestimates(budget_f):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    subaccount = budget_f.create_subaccount(
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


def test_change_subaccount_parent_reestimates(models, budget_f):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    another_account = budget_f.create_account(parent=budget)
    subaccount = budget_f.create_subaccount(
        parent=account,
        rate=1,
        multiplier=5,
        quantity=10
    )
    assert subaccount.nominal_value == 50.0
    assert account.nominal_value == 50.0
    assert budget.nominal_value == 50.0
    assert another_account.nominal_value == 0.0

    ct = models.BudgetAccount if budget_f.domain == 'budget' \
        else models.TemplateAccount
    subaccount.content_type = ContentType.objects.get_for_model(ct)
    subaccount.object_id = another_account.pk
    subaccount.save(update_fields=['content_type', 'object_id'])

    assert subaccount.nominal_value == 50.0
    another_account.refresh_from_db()
    assert another_account.nominal_value == 50.0
    account.refresh_from_db()
    assert account.nominal_value == 0.0
    assert budget.nominal_value == 50.0


@pytest.mark.freeze_time
def test_saving_subaccount_saves_budget(budget_f, freezer, user, staff_user,
        set_model_middleware_user):
    freezer.move_to('2017-05-20')
    budget = budget_f.create_budget(created_by=user)
    account = budget_f.create_account(parent=budget)
    subaccount = budget_f.create_subaccount(parent=account)
    freezer.move_to('2019-05-20')

    # There must be an actively authenticated user that is saving the Account
    # in the context of a request in order for the signals to denote the Budget
    # as having been updated by the user.  We can mimic this by setting the
    # user on the model thread.
    set_model_middleware_user(staff_user)
    subaccount.save()

    budget.refresh_from_db()
    assert budget.updated_at == datetime.datetime(
        2019, 5, 20).replace(tzinfo=timezone.utc)
