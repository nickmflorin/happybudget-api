import pytest

from happybudget.lib.utils.fs import (
    parse_name_and_count, suffix_name_with_count, increment_name_count,
    construct_unique_name)


@pytest.mark.parametrize("value,expected", [
    ("foo(1)", ("foo", 1, "")),
    ("foo", ("foo", None, "")),
    ("foo(2).pdf", ("foo", 2, ".pdf")),
    ("foo.pdf", ("foo", None, ".pdf")),
    ("foo(1)bar(2).pdf", ("foo(1)bar", 2, ".pdf")),
    ("", ("", None, "")),
    ("foo(1.pdf", ("foo(1", None, ".pdf")),
    ("foo1).pdf", ("foo1)", None, ".pdf")),
    ("foo(1-1).pdf", ("foo(1-1)", None, ".pdf")),
    ("(1)", ("", 1, "")),
    ("(1).pdf", ("", 1, ".pdf"))
])
def test_parse_name_and_count(value, expected):
    assert expected == parse_name_and_count(value)


@pytest.mark.parametrize("value,expected", [
    (("foo", 2), "foo(2)"),
    (("foo.pdf", 2), "foo(2).pdf")
])
def test_suffix_name_and_count(value, expected):
    assert expected == suffix_name_with_count(*value)


@pytest.mark.parametrize("value,expected", [
    ("foo", "foo(1)"),
    ("foo.pdf", "foo(1).pdf"),
    ("foo(2)", "foo(3)"),
    ("foo(0)", "foo(1)"),
    ("foo(2).pdf", "foo(3).pdf")
])
def test_increment_name_count(value, expected):
    assert expected == increment_name_count(value)


@pytest.mark.parametrize("data", [
    {
        "name": "foo",
        "names": ["foo", "foo(1)", "Foo(2)"],
        "expected": "foo(2)"
    },
    {
        "name": "foo",
        "names": ["foo", "foo(1)", "Foo(2)"],
        "case_sensitive": False,
        "expected": "foo(3)"
    },
    {
        "name": "foo",
        "names": ["foo.pdf", "foo(3).pdf", "foo(2).jpg"],
        "expected": "foo"
    },
    {
        "name": "foo.pdf",
        "names": ["foo.pdf", "foo(3).pdf", "foo(2).jpg"],
        "expected": "foo(1).pdf"
    },
    {
        "name": "foo.pdf",
        "names": ["foo.pdf", "foo(3).pdf", "foo(2).jpg"],
        "with_extensions": False,
        "expected": "foo(1).pdf"
    },
])
def test_construct_unique_name(data):
    expected = data.pop("expected")
    assert expected == construct_unique_name(**data)
