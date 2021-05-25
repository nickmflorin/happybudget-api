import pytest


@pytest.mark.freeze_time('2020-01-01')
def test_reindex_tags(create_subaccount_unit, freezer):
    units = [
        create_subaccount_unit(order=0),
        create_subaccount_unit(order=1),
        create_subaccount_unit(order=2),
        create_subaccount_unit(order=3),
    ]
    freezer.move_to("2020-01-02")
    units[1].order = 0
    units[1].save()
    [unit.refresh_from_db() for unit in units]
    assert [unit.order for unit in units] == [1, 0, 2, 3]
