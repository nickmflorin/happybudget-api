import datetime
import pytest

from happybudget.app.io.tasks import find_and_delete_empty_attachments


@pytest.mark.freeze_time('2020-01-03 5:50:00')
def test_find_and_delete_empty_attachments(f, models):
    attachments = [
        # Should be deleted since it was > 5min since it was created.
        f.create_attachment(
            name='attachment1.jpeg',
            created_at=datetime.datetime(2020, 1, 3, 5, 44)
                .replace(tzinfo=datetime.timezone.utc)
        ),
        # Should not be deleted because it not empty.
        f.create_attachment(
            name='attachment2.jpeg',
            created_at=datetime.datetime(2020, 1, 3, 5, 44)
                .replace(tzinfo=datetime.timezone.utc)
        ),
        # Should not be deleted because it was < 5min since it was created.
        f.create_attachment(
            name='attachment3.jpeg',
            created_at=datetime.datetime(2020, 1, 3, 5, 49)
                .replace(tzinfo=datetime.timezone.utc)
        ),
        # Should not be deleted because it not empty.
        f.create_attachment(
            name='attachment4.jpeg',
            created_at=datetime.datetime(2020, 1, 3, 5, 44)
                .replace(tzinfo=datetime.timezone.utc)
        ),
        # Should not be deleted because it not empty.
        f.create_attachment(
            name='attachment4.jpeg',
            created_at=datetime.datetime(2020, 1, 3, 5, 44)
                .replace(tzinfo=datetime.timezone.utc)
        ),
    ]
    f.create_contact(attachments=[attachments[1]])
    budget = f.create_budget()
    account = f.create_account(parent=budget)
    f.create_actual(budget=budget, attachments=[attachments[3]])
    f.create_subaccount(
        parent=account,
        attachments=[attachments[4]]
    )

    find_and_delete_empty_attachments()
    assert models.Attachment.objects.count() == 4
