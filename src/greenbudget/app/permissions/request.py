from rest_framework import permissions


def request_is_write_method(request):
    return not request_is_safe_method(request)


def request_is_safe_method(request):
    return request.method in permissions.SAFE_METHODS


def request_is_admin(request):
    return '/admin/' in request.path
