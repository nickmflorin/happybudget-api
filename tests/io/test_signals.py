import pytest

from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError


def test_empty_attachments_deleted(create_budget, create_attachment,
        create_budget_account, create_actual, create_budget_subaccount):
    budget = create_budget()
    account = create_budget_account(parent=budget)
    attachments = [
        create_attachment(name='attachment1.jpeg'),
        create_attachment(name='attachment2.jpeg'),
        create_attachment(name='attachment3.jpeg')
    ]
    account = create_budget_account(parent=budget)
    subaccount = create_budget_subaccount(
        parent=account,
        attachments=attachments,
    )
    actual = create_actual(
        budget=budget,
        attachments=[attachments[0], attachments[2]]
    )
    actual.attachments.remove(attachments[0])
    attachments[0].refresh_from_db()
    subaccount.attachments.remove(attachments[0])

    with pytest.raises(ObjectDoesNotExist):
        attachments[0].refresh_from_db()


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
