from collections import OrderedDict
from urllib.parse import urlsplit, parse_qsl, urlunsplit, urlencode

from django.http import QueryDict


def parse_ids_from_request(request, param='ids'):
    """
    Parses and validates a given set of numeric IDs from the query parameters
    of a request.
    """
    ids = request.query_params.get(param, None)
    if ids is not None:
        if ids.startswith('[') and ids.endswith(']'):
            ids = ids[1:-1]
        ids = [id.strip() for id in ids.split(',')]
        numeric_ids = []
        has_invalid = False
        for check_id in ids:
            try:
                numeric_ids.append(int(check_id))
            except ValueError:
                has_invalid = True
        # Only return None if there were IDs in the request but none of them
        # were valid.  If the included set of IDs was actually an empty list,
        # we want to return an empty list.
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
