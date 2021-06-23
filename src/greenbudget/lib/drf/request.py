def is_truthy(value):
    return value in (1, 'True', 'true', True)


def parse_boolean_query_params(request, *params):
    return {k: is_truthy(request.GET[k]) for k in params if k in request.GET}
