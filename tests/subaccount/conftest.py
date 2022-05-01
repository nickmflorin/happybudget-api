import pytest


@pytest.fixture
def units(f):
    return [
        f.create_subaccount_unit(title='Days'),
        f.create_subaccount_unit(title='Weeks')
    ]
