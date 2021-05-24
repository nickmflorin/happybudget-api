def test_reindex_tags(create_subaccount_unit):
    units = [
        create_subaccount_unit(order=0),
        create_subaccount_unit(order=1),
        create_subaccount_unit(order=2),
        create_subaccount_unit(order=3),
    ]
    units[1].order = 0
    units[1].save()

    [unit.refresh_from_db() for unit in units]
    assert [unit.order for unit in units] == [1, 0, 2, 3]
