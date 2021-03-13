import pytest


@pytest.mark.freeze_time('2020-01-01')
def test_get_contacts(api_client, create_contact):
    import ipdb
    ipdb.set_trace()
