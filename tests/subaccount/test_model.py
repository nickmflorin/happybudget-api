from django.db import IntegrityError
import pytest


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
