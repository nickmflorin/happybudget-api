import pytest


@pytest.fixture
def units(create_subaccount_unit):
    return [
        create_subaccount_unit(title='Days'),
        create_subaccount_unit(title='Weeks')
    ]
