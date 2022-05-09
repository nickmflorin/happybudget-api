from rest_framework import exceptions


class PermissionErrorCodes:
    PERMISSION_ERROR = "permission_error"
    PRODUCT_PERMISSION_ERROR = "product_permission_error"


class PermissionErr(exceptions.PermissionDenied):
    default_code = PermissionErrorCodes.PERMISSION_ERROR
