class ProductPermissionIdMixin:
    def __init__(self, **kwargs):
        if 'permission_id' not in kwargs \
                and getattr(self, 'default_permission_id', None) is None:
            self.raise_permission_id_not_available()
        self._permission_id = kwargs.get('permission_id', None)

    def raise_permission_id_not_available(self):
        raise Exception(
            "%s cannot be set with a null permission ID if no default "
            "permission ID is defined on the class."
            % self.__class__.__name__
        )

    @property
    def permission_id(self):
        if self._permission_id is None:
            if getattr(self, 'default_permission_id', None) is None:
                self.raise_permission_id_not_available()
            return self.default_permission_id
        return self._permission_id

    @permission_id.setter
    def permission_id(self, value):
        if value is None:
            if getattr(self, 'default_permission_id', None) is None:
                self.raise_permission_id_not_available()
            setattr(self, '_permission_id', None)
        else:
            setattr(self, '_permission_id', value)
