from happybudget.lib.utils import ensure_iterable


class DisallowedField:
    def __init__(self, **kwargs):
        self._attribute = ensure_iterable(
            kwargs.get('attribute'), cast_none=False)
        self._cls = ensure_iterable(kwargs.get('cls'), cast_none=False)
        self._name = ensure_iterable(kwargs.get('name'), cast_none=False)
        self._conditional = kwargs.get('conditional')

    def field_cls_is_disallowed(self, field):
        if self._cls is not None:
            return type(field) in self._cls
        return None

    def field_name_is_disallowed(self, field):
        if self._name is not None:
            return field.name in self._name
        return None

    def field_conditional_is_disallowed(self, field):
        if self._conditional is not None:
            return type(field) in ensure_iterable(self._conditional['cls']) \
                and self._conditional['disallowed'](field)
        return None

    def field_attribute_is_disallowed(self, field):
        if self._attribute is not None:
            return any([
                getattr(field, attr[0], None) == attr[1]
                for attr in self._attribute
            ])
        return None

    def is_disallowed(self, field):
        evaluated = [result for result in [
            self.field_cls_is_disallowed(field),
            self.field_name_is_disallowed(field),
            self.field_conditional_is_disallowed(field),
            self.field_attribute_is_disallowed(field)
        ] if isinstance(result, bool)]
        return len(evaluated) != 0 and all(evaluated)


class AllowedFieldOverride:
    def __init__(self, name, cls, conditional=None):
        self._name = name
        self._cls = cls
        self._conditional = conditional

    def is_overridden(self, field, value, user):
        overridden = field.name == self._name and type(field) is self._cls
        if overridden and self._conditional is not None:
            return self._conditional(value, user)
        return overridden
