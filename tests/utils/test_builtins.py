import pytest

from greenbudget.lib.utils.builtins import get_string_formatted_kwargs


@pytest.mark.parametrize('string,expected', [
    ('This is a {argument1} string that is formatted with {argument2}.', [
     'argument1', 'argument2']),
    ('This is a {argument1} string that is formatted with {argument2.', [
     'argument1']),
    ('This is a argument1} string that is formatted with {argument2}.', [
     'argument2'])
])
def test_get_string_formatted_kwargs(string, expected):
    result = get_string_formatted_kwargs(string)
    assert result == expected
