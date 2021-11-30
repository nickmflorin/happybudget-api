import pytest

from greenbudget.app.tabling.utils import (
    lexographic_midpoint, InconsistentOrderingError)


@pytest.mark.parametrize('a,b,expected', [
    ('aaa', 'bbb', 'bban'),
    ('aab', 'aad', 'aac'),
    ('a', 'c', 'b'),
    ('abcd', 'abf', 'abe'),
    # # Cases where the first differing characters are consecutive.
    ('abh', 'abit', 'abhn'),
    ('abhs', 'abit', 'abhw'),
    ('abhz', 'abit', 'abhzn'),
    ('abhzs', 'abit', 'abhzw'),
    ('abhzz', 'abit', 'abhzzn'),
    # Cases where the right string will have(a, b) as differing character.
    ('abc', 'abcah', 'abcad'),
    ('abc', 'abcab', 'abcaan'),
    ('abc', 'abcaah', 'abcaad'),
    ('abc', 'abcb', 'abcan'),
    ('abc', 'abcbfg', 'abcbc'),
    ('abc', None, 'n'),
    (None, 'abc', 'abbn'),
    ('a', None, 'n'),
    (None, 'a', InconsistentOrderingError),
    ('ynt', None, 'yntw'),
    ('y', 'z', 'yn'),
    ('ynqnt', 'ynr', 'ynqt')
])
def test_lexographic_midpoint(a, b, expected):
    if isinstance(expected, str):
        result = lexographic_midpoint(a, b)
        assert result == expected
    else:
        with pytest.raises(expected):
            result = lexographic_midpoint(a, b)
