class ProductPermissionIdMixin:
    def __init__(self, **kwargs):
        if 'permission_id' not in kwargs \
                and getattr(self, 'default_permission_id', None) is None:
            raise Exception(
                "%s cannot be set with a null permission ID if no default "
                "permission ID is defined on the class."
                % self.__class__.__name__
            )
        self._permission_id = kwargs.get('permission_id', None)

    @property
    def permission_id(self):
        if self._permission_id is None:
            # This should be enforced via the setter.
            assert hasattr(self, 'default_permission_id')
            return self.default_permission_id
        return self._permission_id

    @permission_id.setter
    def permission_id(self, value):
        if value is None:
            if getattr(self, 'default_permission_id', None) is None:
                raise Exception(
                    "%s cannot be set with a null permission ID if no default "
                    "permission ID is defined on the class."
                    % self.__class__.__name__
                )
            setattr(self, '_permission_id', None)
        else:
            setattr(self, '_permission_id', value)
