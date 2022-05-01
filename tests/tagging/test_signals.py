import pytest


@pytest.mark.freeze_time('2020-01-01')
def test_reindex_tags(f, freezer):
    units = [
        f.create_subaccount_unit(order=0, title="A"),
        f.create_subaccount_unit(order=1, title="B"),
        f.create_subaccount_unit(order=2, title="C"),
        f.create_subaccount_unit(order=3, title="D"),
    ]
    freezer.move_to("2020-01-02")
    units[1].order = 0
    units[1].save()
    # pylint: disable=expression-not-assigned
    [unit.refresh_from_db() for unit in units]
    assert [unit.order for unit in units] == [1, 0, 2, 3]
