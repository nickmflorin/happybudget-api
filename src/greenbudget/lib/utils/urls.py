from collections import OrderedDict
import os
from urllib.parse import urlsplit, parse_qsl, urlunsplit, urlencode

from django.conf import settings
from django.http import QueryDict

from .builtins import find_string_formatted_arguments


__all__ = (
    'get_base_url',
    'get_query_params',
    'add_query_params_to_url',
    'relativize_url',
    'make_url_absolute',
    'relative_path_join',
    'safe_format_url',
    'parse_ids_from_request'
)


def parse_ids_from_request(request):
    ids = request.query_params.get('ids', None)
    if ids is not None:
        if ids.startswith('[') and ids.endswith(']'):
            ids = ids[1:-1]
        ids = [id.strip() for id in ids.split(',')]
        numeric_ids = []
        has_invalid = False
        for id in ids:
            try:
                numeric_ids.append(int(id))
            except ValueError:
                has_invalid = True
        if len(numeric_ids) == 0 and has_invalid:
            return None
        return numeric_ids
    return None


def get_base_url(url):
    """
    Returns the URL with query parameters and fragment removed.
    """
    scheme, netloc, path, _, _ = urlsplit(url)
    return urlunsplit([scheme, netloc, path, None, None])


def get_query_params(url, mutable=False, as_dict=False):
    """
    Returns query parameters found in a URL as an OrderedDict.
    """
    query_dict = QueryDict(urlsplit(url).query, mutable=mutable)
    if as_dict:
        return query_dict.dict()
    return query_dict


def add_query_params_to_url(url, **params):
    """
    Returns a URL with the given query parameters appended to it.

    Existing query parameters will be merged with the provided query
    parameters if they exist on the URL.

    Usage:
    -----
    >>> add_query_params_to_url("https://google.com?a=1", b=2, c=3)
    >>> "https://google.com?a=1&b=2&c=3"
    """
    scheme, netloc, path, query_string, fragment = urlsplit(url)
    query = OrderedDict(parse_qsl(query_string))
    query.update(**params)
    query_string = urlencode(query)
    return urlunsplit([scheme, netloc, path, query_string, fragment])


def relative_path_join(*paths):
    """
    Joins a series of paths together.  If any given path after the base
    includes a leading slash, the path will be joined without that leading
    slash.

    This solves the following problem:

    >>> os.path.join("https://google.com/v1", "/services")
    >>> "/services"

    With this method, all paths after the base are considered to be relative
    to the base.
    """
    base_path = paths[0]
    for additional_path in list(paths)[1:]:
        if additional_path == "/":
            raise ValueError("Relative paths cannot be `/`.")
        if additional_path.startswith("/"):
            base_path = os.path.join(base_path, additional_path[1:])
        else:
            base_path = os.path.join(base_path, additional_path)
    return base_path


def safe_format_url(url, **kwargs):
    """
    Formats the URL with the provided arguments if and only if each argument
    is in the URL as {arg_name}.

    This avoids the following error:

    >>> value = "/services/{service}/{id}"
    >>> value.format(service='test')
    >>> KeyError: 'id'

    Instead, this method produces the following:

    >>> value = "/services/{service}/{id}"
    >>> safe_format_url(service='test')
    >>> "/services/test/{id}"
    """
    arguments = find_string_formatted_arguments(url)
    safe_kwargs = {}
    for argument in arguments:
        if argument in kwargs:
            safe_kwargs[argument] = kwargs[argument]
        else:
            safe_kwargs[argument] = "{%s}" % argument
    return url.format(**safe_kwargs)


def make_url_absolute(url, request=None, domain=None, scheme=None, base=None):
    """
    Makes the provided URL absolute by prepending the scheme and domain
    of either the APP_URL defined in settings, the provided
    base URL or the explicitly provided values.

    Parameters:
    ----------
    url: :obj:`str`
        The URL that should be made absolute.

    request: :obj:`requests.Request` (optional)
        A :obj:`requests.Request` that can be used to infer the scheme and/or
        domain.

    base: :obj:`str` (optional)
        A base URL that should be used to determine the domain and the scheme.
        The base URL can have paths affixed.

        >>> make_url_absolute("/endpoint", base="https://greenbudget.io/v1)
        >>> "https://greenbudget.io/v1/endpoint"

    scheme: :obj:`str` (optional)
        The explicitly provided scheme to use for the constructed absolute
        URL.

        One of "https" or "http".

    domain: :obj:`str` (optional)
        The explicitly provided domain to use for the constructed absolute
        URL.  The domain must not have the scheme included.

    Usage:
    -----
    >>> make_url_absolute("/v1/budgets/5", domain="localhost:8000",
    >>>    scheme="http")
    >>> "http://localhost:8000/v1/budgets/5"

    >>> make_url_absolute("/v1/budgets/5")
    >>> "https://greenbudget.io/v1/budgets/5"
    """
    url_scheme, netloc, path, query_string, fragment = urlsplit(url)
    if url_scheme and netloc:
        return url

    scheme = url_scheme
    if not scheme:
        scheme = urlsplit(settings.APP_URL).scheme

    if netloc:
        domain = netloc
    elif domain is not None:
        if '://' in domain:
            raise ValueError(
                "Domains should not contain a scheme "
                "(ie, www.example.com not http://www.example.com/)."
            )
        domain = domain.rstrip('/')
    elif base is not None:
        base_path = urlsplit(base).path
        # If the base path is the root, the path of the provided URL should
        # be used.  If the path of the provided URL is the root, the base
        # path should be used.
        if base_path != "/":
            if path != "/":
                path = relative_path_join(urlsplit(base).path, path)
            else:
                path = base_path
        domain = urlsplit(base).netloc
        scheme = urlsplit(base).scheme
        if not scheme:
            raise Exception("The base URL must include the scheme.")
    elif request is not None:
        domain = request.get_host()
        if not scheme:
            scheme = "http%s" % ("s" if request.is_secure() else "")
    else:
        domain = urlsplit(settings.APP_URL).netloc

    return urlunsplit((scheme, domain, path, query_string, fragment))


def relativize_url(url):
    """
    Relativizes a URL by removing the scheme and netloc, if the netloc is
    the same as the APP_URL.

    Usage:
    -----
    >>> relativize_url("https://greenbudget.io/v1/budgets/5")
    >>> "/v1/documents"

    >>> relativize_url("https://google.ai/v1/budgets/5")
    >>> "https://google.ai/v1/budgets/5"
    """
    scheme, netloc, path, query_string, fragment = urlsplit(url)
    possible_netloc = urlsplit(settings.APP_URL)[1]
    if netloc != possible_netloc:
        return url
    return urlunsplit(['', '', path, query_string, fragment])
