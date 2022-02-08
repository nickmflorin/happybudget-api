from greenbudget.lib.drf.fields import GenericRelatedField

from .exceptions import InvalidToken


class ShareTokenInstanceField(GenericRelatedField):
    """
    An extension of :obj:`GenericRelatedField` that will forcefully raise an
    authenticated related error if the generic instance does not exist or the
    provided type is invalid.

    This is important because when validating whether or not a :obj:`ShareToken`
    is valid for a given instance, the `type` and `id` are included in the
    request to indicate what instance the token is referring to.  The `id`
    field is pulled directly from the URL, so it can be anything - and we want
    to ensure that the FE is aware that the token authentication failed based
    on invalid ID path parameters in the FE URL.
    """

    def fail(self, key, **kwargs):
        if key == 'does_not_exist':
            raise InvalidToken()
        return super().fail(key, **kwargs)
