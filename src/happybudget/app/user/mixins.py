from django.conf import settings
from django.core.exceptions import FieldDoesNotExist
from django.db import IntegrityError, models

from happybudget.lib.utils import get_attribute
from happybudget.app import exceptions, permissions


def get_ownership_field(klass):
    assert hasattr(klass, 'user_ownership_field'), \
        f"The class {klass} does not support user ownership."
    assert klass.user_ownership_field is not None, \
        f"The model {klass} does not define a means of making " \
        "ownership determination."
    return klass.user_ownership_field


def get_owner(obj):
    # pylint: disable=import-outside-toplevel
    from .models import User
    field = get_ownership_field(obj.__class__)
    owner = get_attribute(field, obj, delimiter='__')
    if owner is None or not isinstance(owner, User):
        raise InvalidUserOwnershipField(field=field)
    return owner


class InvalidUserOwnershipField(Exception):
    def __init__(self, klass=None, field=None):
        assert klass is not None or field is not None, \
            "Either the class that dictates ownership or the field itself " \
            "must be provided."
        self._field = field
        if klass is not None and field is None:
            self._field = get_ownership_field(klass)

    def __str__(self):
        return (
            "The user ownership field "
            f"{self._field} does not point to a valid User model."
        )


class SupportsDbLookup:
    """
    Returns whether or not the field dictated by `user_ownership_field` is
    composed of model database fields that can be used for queryset filtering
    and lookup.  This includes both cases where the `user_ownership_field` value
    is associated with a single, non-related field and cases where the
    `user_ownership_field` value is composed of sub-fields that are separated
    by "__" and point to the single, non-related field of a related field model
    (i.e. <field_1>__<field_2>).

    There are cases where the `user_ownership_field` points to an attribute
    of the model class that is not a database field.  In those cases, the
    queryset filter or lookup cannot be performed and this descriptor will
    indicate as such.

    In order for the `user_ownership_field` to support queryset filtering and
    lookup, each field separated by the __ notation needs to be an instance of
    :obj:`django.db.models.ForeignKey` with the last (or only) field separated
    by the __ being a :obj:`django.db.models.ForeignKey` field that points to
    the :obj:`User` model.

    Ex.
    ---
    In the example shown below, ModelB would support database queryset filtering
    and lookup for the field "model_b__created_by".  This is because "model_b"
    is associated with a ForeignKey and that ForeignKey points to a model that
    has a "created_by" field that is also a ForeignKey, but points to a User.

    Additionally, ModelA would support database queryset filtering and lookup
    for the field "created_by", since the attribute associated with "created_by"
    is in fact a valid instance of :obj:`django.db.models.ForeignKey` that points
    to the User model.

    class ModelA(models.Model):
        created_by = models.ForeignKey(to=User, ...)

    class ModelB(models.Model):
        model_b = models.ForeignKey(to=ModelA, ...)

    Note:
    ----
    The logic used in this implementation is not foolproof for all cases of
    determining whether or not a field lookup for a given model is valid, but
    only the case of determining whether or not the field associated with user
    ownership is a valid field lookup for querying and filtering.  This is
    because there are other related fields where table joins defined by a
    "__" separated field string are valid.  For instance, a
    :obj:`django.db.models.ManyToMany` field could be referenced by a part of
    the "__" separated field name string.  However, as it relates to defining
    user ownership, this will never be the case since user ownership fields
    have to eventually point to a single User model instance.
    """
    def __get__(self, obj, objtype=None):
        # pylint: disable=import-outside-toplevel
        from .models import User

        klass = objtype
        if klass is None:
            klass = obj.__class__
        assert klass.user_ownership_field is not None, \
            f"The model {klass} does not define a means of making " \
            "ownership determination."

        parts = klass.user_ownership_field.split('__')

        # Keep track of the model class that the current related field refers
        # to.
        running_klass = klass
        for i, v in enumerate(parts):
            try:
                fld = running_klass._meta.get_field(v)
            except FieldDoesNotExist:
                # We do not want to raise a hard exception if the field does
                # not exist because the field could be referring to an attribute
                # of the model instead of a database field.
                return False
            else:
                # All sub-fields must be a ForeignKey, either pointing to
                # another model or pointing to the User model (in the case it
                # is the last subfield).
                if not isinstance(fld, models.ForeignKey):
                    return False
                # If we are at the last sub-field, the field must be a
                # ForeignKey pointing to the User model.
                if i == len(parts) - 1:
                    to_model = fld.related_fields[0][1].model
                    # Here, if the ForeignKey does not point to a User this is
                    # an invalid `user_ownership_field` and an exception should
                    # be raised instead of returning False.
                    if to_model is not User:
                        raise InvalidUserOwnershipField(klass=klass)
                    return True
                # At this point, we know that we are dealing with a ForeignKey
                # field that is not the last field in a "__" separated string.
                # In this case, the `related_fields` attribute of the field will
                # be field itself followed by the primary key field that it is
                # linked to.  That primary key field will be associated with the
                # model that the foreign key points to.
                # [(<django.db.models.fields.related.ForeignKey: parent>,
                #   <django.db.models.fields.AutoField: id>)]
                running_klass = fld.related_fields[0][1].model
        return True


class ModelOwnershipMixin:
    user_ownership_field = None
    supports_owner_db_lookup = SupportsDbLookup()

    class Meta:
        abstract = True

    def has_same_owner(self, obj, raise_exception=False):
        assert type(obj) is not type(self), \
            "Ownership comparison is only meant to be performed on instances " \
            "of different classes."
        owner = get_owner(obj)
        result = self.is_owned_by(owner)
        if not result and raise_exception:
            raise IntegrityError(
                f"Instance {obj.pk} of model {obj.__class__.__name__} does not "
                f"have the same ownership as instance {self.pk} of model "
                f"{self.__class__.__name__}."
            )
        return result

    def is_owned_by(self, user, raise_exception=False):
        result = self.user_owner == user
        if not result and raise_exception:
            raise IntegrityError(
                f"Instance {self.pk} of model {self.__class__.__name__} does "
                f"not have the correct owner: {user.pk}."
            )
        return result

    @classmethod
    def raise_owner_db_lookup_not_supported(cls, raise_exception=True):
        if not cls.supports_owner_db_lookup:
            if not raise_exception:
                return False
            raise IntegrityError(
                f"The model {cls.__name__} is associated with a user ownership "
                f"field {cls.user_ownership_field} that does not support "
                "database lookup."
            )
        return True

    @property
    def user_owner(self):
        return get_owner(self)

    @property
    def owner_is_staff(self):
        return self.user_owner.is_staff


class UserAuthenticationMixin:
    @property
    def is_fully_authenticated(self):
        return self.can_authenticate(raise_exception=False)

    def has_permissions(self, **kwargs):
        """
        A method to evaluate a set of permissions that extend
        :obj:`UserPermission` for a given :obj:`User`.
        """
        pms = kwargs.pop(
            'permissions',
            settings.REST_FRAMEWORK['DEFAULT_PERMISSION_CLASSES']
        )
        default_exception_class = kwargs.pop(
            'default_exception_class', exceptions.PermissionErr)
        raise_exception = kwargs.pop('raise_exception', True)
        hard_raise = kwargs.pop('hard_raise', False)

        for permission in permissions.instantiate_permissions(pms):
            assert hasattr(permission, 'has_user_perm'), \
                f"The permission class {permission.__class__} does not have a " \
                "user permission method."
            try:
                has_permission = permission.has_user_perm(
                    self,
                    raise_exception=True,
                    hard_raise=hard_raise
                )
            except (
                exceptions.PermissionErr,
                exceptions.NotAuthenticatedError
            ) as e:
                if raise_exception:
                    raise e
                return False
            if not has_permission:
                if raise_exception:
                    raise default_exception_class(
                        detail=getattr(permission, 'message', None),
                        hard_raise=hard_raise
                    )
                return False
        return True

    def can_authenticate(self, **kwargs):
        return self.has_permissions(
            default_exception_class=exceptions.NotAuthenticatedError,
            permissions=settings.AUTHENTICATION_PERMISSION_CLASSES,
            **kwargs
        )
