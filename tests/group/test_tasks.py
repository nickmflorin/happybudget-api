import datetime
import pytest

from happybudget.app.group.tasks import find_and_delete_empty_groups


@pytest.mark.freeze_time('2020-01-03 5:50:00')
def test_find_and_delete_empty_groups(f, models):
    budget = f.create_budget()
    groups = [
        # Should be deleted since it was > 5min since it was created.
        f.create_group(
            parent=budget,
            created_at=datetime.datetime(2020, 1, 3, 5, 44)
                .replace(tzinfo=datetime.timezone.utc)
        ),
        # Should not be deleted because it not empty.
        f.create_group(
            parent=budget,
            created_at=datetime.datetime(2020, 1, 3, 5, 44)
                .replace(tzinfo=datetime.timezone.utc)
        ),
        # Should not be deleted because it was < 5min since it was created.
        f.create_group(
            parent=budget,
            created_at=datetime.datetime(2020, 1, 3, 5, 49)
                .replace(tzinfo=datetime.timezone.utc)
        )
    ]
    f.create_budget_account(parent=budget, group=groups[1])
    find_and_delete_empty_groups()
    assert models.Group.objects.count() == 2
