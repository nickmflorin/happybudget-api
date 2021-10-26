import pytest

from django.db import IntegrityError


@pytest.mark.freeze_time('2020-01-01')
def test_subaccount_attachment_invalid_created_by(admin_user, create_budget,
        create_budget_account, create_budget_subaccount, create_attachment):
    budget = create_budget()
    account = create_budget_account(parent=budget)
    attachments = [
        create_attachment(name='attachment1.jpeg'),
        create_attachment(name='attachment2.jpeg'),
        create_attachment(name='attachment3.jpeg', created_by=admin_user)
    ]
    with pytest.raises(IntegrityError):
        create_budget_subaccount(
            parent=account,
            attachments=attachments
        )


@pytest.mark.freeze_time('2020-01-01')
def test_actual_attachment_invalid_created_by(admin_user, create_budget,
        create_actual, create_attachment):
    budget = create_budget()
    attachments = [
        create_attachment(name='attachment1.jpeg'),
        create_attachment(name='attachment2.jpeg'),
        create_attachment(name='attachment3.jpeg', created_by=admin_user)
    ]
    with pytest.raises(IntegrityError):
        create_actual(
            budget=budget,
            attachments=attachments
        )
