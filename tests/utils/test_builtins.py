from greenbudget.lib.utils import (
    find_string_formatted_arguments, find_in_dict, place_in_dict)


def test_find_in_dict():
    data = {'foo': {'bar': {'banana': 'pear'}}}
    assert find_in_dict(data, 'foo') == {'bar': {'banana': 'pear'}}
    assert find_in_dict(data, ['foo', 'bar']) == {'banana': 'pear'}
    assert find_in_dict(data, ['foo', 'bar', 'banana']) == 'pear'


def test_place_in_dict():
    data = {'foo': {'bar': {'banana': 'pear'}}}

    place_in_dict(data, 'foo', {'apple': {'bar': 'banana'}})
    assert data == {'foo': {'apple': {'bar': 'banana'}}}

    place_in_dict(data, ['foo', 'apple'], {'bat': 'pear'})
    assert data == {'foo': {'apple': {'bat': 'pear'}}}

    place_in_dict(data, ['foo', 'apple', 'bat'], 'banana')
    assert data == {'foo': {'apple': {'bat': 'banana'}}}


def test_find_string_formatted_arguments():
    string_no_arguments = "Lorem ipsum lorem ipsum."
    arguments = find_string_formatted_arguments(string_no_arguments)
    assert arguments == []

    string_arguments = "Lorem ipsum {arg1} lorem ipsum {arg2}."
    arguments = find_string_formatted_arguments(string_arguments)
    assert arguments == ['arg1', 'arg2']
