import pytest

from django.http import QueryDict
from django.test import override_settings

from greenbudget.lib.utils.urls import (
    add_query_params_to_url, get_query_params, get_base_url,
    relativize_url, make_url_absolute, safe_format_url)


def test_safe_format_url():
    url = "https://greenbudget.io/services/{service}/{id}"
    formatted = safe_format_url(url, service="test")
    assert formatted == "https://greenbudget.io/services/test/{id}"

    formatted = safe_format_url(url, service='test', id=5)
    assert formatted == "https://greenbudget.io/services/test/5"


class TestMakeUrlAbsolute:
    @override_settings(APP_URL="https://greenbudget.com")
    def test_make_url_absolute(self):
        """
        If the request and the explicit scheme/domain are not provided, the
        URL should be made absolute in the context of the APP_URL
        in settings.
        """
        absolute_url = make_url_absolute("/api/document/5")
        assert absolute_url == "https://greenbudget.com/api/document/5"

    def test_make_url_absolute_explicit_scheme_domain(self):
        """
        If the scheme and/or domain are explicitly provided, they should be
        used over the domain/scheme of the APP_URL in settings.
        """
        absolute_url = make_url_absolute(
            "/api/document/5",
            scheme="http",
            domain="google.com"
        )
        assert absolute_url == "https://google.com/api/document/5"

    @override_settings(APP_URL="https://greenbudget.com")
    def test_make_absolute_url_absolute(self):
        """
        If the URL is already absolute, the URL should be unchanged.
        """
        absolute_url = make_url_absolute(
            "https://greenbudget.com/api/document/5")
        assert absolute_url == "https://greenbudget.com/api/document/5"


class TestRelativizeUrl:
    @override_settings(APP_URL="https://greenbudget.com")
    def test_relativize_greenbudget_url_different_scheme(self):
        """
        If the scheme differs from the APP_URL in settings, the
        URL should still be relativized.
        """
        relativized_url = relativize_url(
            "http://greenbudget.com/api/document/5")
        assert relativized_url == "/api/document/5"

    @override_settings(APP_URL="http://greenbudget.com")
    def test_relativize_greenbudget_url(self):
        """
        If the URL is absolute in the context of the APP_URL, the
        URL relative to that scheme/domain should be returned.
        """
        relativized_url = relativize_url(
            "http://greenbudget.com/api/document/5")
        assert relativized_url == "/api/document/5"

    @override_settings(APP_URL="http://greenbudget.com")
    def test_relativize_url_different_netloc(self):
        """
        If the URL is absolute in the context of another domain, the URL
        should be unchanged.
        """
        relativized_url = relativize_url("http://google.com/api/document/5")
        assert relativized_url == "http://google.com/api/document/5"


class TestGetBaseUrl:
    base_url = 'https://www.google.com/foo/bar/'
    query_string = '?baz=1&x=y'
    fragment = '#clickme'

    def test_removes_fragment_and_querystring(self):
        """
        If the URL contains both query string parameters and a fragment,
        get_base_url() should return a URL without them.
        """
        url = self.base_url + self.query_string + self.fragment
        assert get_base_url(url) == self.base_url

        # Should still work without a trailing slash.
        url = self.base_url[:-1] + self.query_string + self.fragment
        assert get_base_url(url) == self.base_url[:-1]

    def test_removes_fragment(self):
        """
        If the URL contains a fragment, get_base_url() should return a URL
        without the fragment.
        """
        url = self.base_url + self.fragment
        assert get_base_url(url) == self.base_url

        # Should still work without a trailing slash.
        url = self.base_url[:-1] + self.fragment
        assert get_base_url(url) == self.base_url[:-1]

    def test_removes_query_string(self):
        """
        If the URL contains query string parameters, get_base_url() should
        return a URL without them.
        """
        url = self.base_url + self.query_string
        assert get_base_url(url) == self.base_url

        # Should still work without a trailing slash.
        url = self.base_url[:-1] + self.query_string
        assert get_base_url(url) == self.base_url[:-1]


class TestGetQueryParams:
    base_url = 'https://www.google.com/foo/bar/'

    def test_empty(self):
        """
        If the url has no query params, get_query_params() should return an
        empty QueryDict instance.
        """
        url = self.base_url
        params = get_query_params(url)
        assert params.dict() == {}

    def test_default_immutable(self):
        """
        By default, the QueryDict returned from get_query_params() should not
        be mutable.
        """
        url = self.base_url + '?baz=1&x=y'
        params = get_query_params(url)
        with pytest.raises(AttributeError):
            params['baz'] = '2'

    def test_can_be_mutable(self):
        """
        Passing `mutable=True` into get_query_params() should create a QueryDict
        instance that we are allowed to mutate.
        """
        url = self.base_url + '?baz=1&x=y'
        params = get_query_params(url, mutable=True)
        params['baz'] = '2'
        assert params.dict() == {'baz': '2', 'x': 'y'}

    def test_default_is_query_dict(self):
        """
        By default, get_query_params() should return a QueryDict instance, not
        a dict instance.
        """
        url = self.base_url + '?baz=1&x=y'
        params = get_query_params(url)
        assert isinstance(params, QueryDict)

    def test_returns_dict(self):
        """
        Specifying `as_dict = True` for get_query_params() should result in
        a mutable dict instance being returned.
        """
        url = self.base_url + '?baz=1&x=y'
        params = get_query_params(url, mutable=False, as_dict=True)
        assert isinstance(params, dict)

    def test_multiple_params(self):
        """
        If multiple parameter values exist for single key in query_string,
        the QueryDict returned should return the last value for __getitem__,
        but should still return the full list using the .get_list() method.

        If the QueryDict is converted to a dict(), than the value should be
        the last value set.
        """
        url = self.base_url + '?baz=1&x=y&baz=5'
        params = get_query_params(url)

        assert params['baz'] == '5'
        assert params.getlist('baz') == ['1', '5']

        params = get_query_params(url, as_dict=True)
        assert params['baz'] == '5'


class TestAddQueryParams:
    def test_add_query_param(self):
        """
        Query params should be appended to URL.
        """
        url = add_query_params_to_url('http://www.example.com/foo/',
            spam='eggs')
        assert url == 'http://www.example.com/foo/?spam=eggs'

    def test_add_query_param_existing_params(self):
        """
        Existing URLs should not be changed when new params are added.
        """
        url = add_query_params_to_url('http://www.example.com/foo/?page=1',
            spam='eggs')
        assert url == 'http://www.example.com/foo/?page=1&spam=eggs'

    def test_add_query_param_relative_url(self):
        """
        Query params should be appended to relative URLs.
        """
        url = add_query_params_to_url('/foo/', spam='eggs')
        assert url == '/foo/?spam=eggs'
