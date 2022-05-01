import pytest

from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError


def test_empty_attachments_deleted(f):
    budget = f.create_budget()
    account = f.create_budget_account(parent=budget)
    attachments = [
        f.create_attachment(name='attachment1.jpeg'),
        f.create_attachment(name='attachment2.jpeg'),
        f.create_attachment(name='attachment3.jpeg')
    ]
    account = f.create_budget_account(parent=budget)
    subaccount = f.create_budget_subaccount(
        parent=account,
        attachments=attachments,
    )
    actual = f.create_actual(
        budget=budget,
        attachments=[attachments[0], attachments[2]]
    )
    actual.attachments.remove(attachments[0])
    attachments[0].refresh_from_db()
    subaccount.attachments.remove(attachments[0])

    with pytest.raises(ObjectDoesNotExist):
        attachments[0].refresh_from_db()


def test_subaccount_attachment_invalid_created_by(admin_user, f):
    budget = f.create_budget()
    account = f.create_budget_account(parent=budget)
    attachments = [
        f.create_attachment(name='attachment1.jpeg'),
        f.create_attachment(name='attachment2.jpeg'),
        f.create_attachment(name='attachment3.jpeg', created_by=admin_user)
    ]
    with pytest.raises(IntegrityError):
        f.create_budget_subaccount(
            parent=account,
            attachments=attachments
        )


def test_actual_attachment_invalid_created_by(admin_user, f):
    budget = f.create_budget()
    attachments = [
        f.create_attachment(name='attachment1.jpeg'),
        f.create_attachment(name='attachment2.jpeg'),
        f.create_attachment(name='attachment3.jpeg', created_by=admin_user)
    ]
    with pytest.raises(IntegrityError):
        f.create_actual(
            budget=budget,
            attachments=attachments
        )
