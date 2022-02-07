from greenbudget.app import permissions


class IsDomain(permissions.BasePermission):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._domain = kwargs.pop('domain')

    def has_permission(self, request, view):
        return False

    def has_object_permission(self, request, view, obj):
        return obj.domain == self._domain


class IsBudgetDomain(IsDomain):
    def __init__(self, *args, **kwargs):
        kwargs['domain'] = 'budget'
        super().__init__(*args, **kwargs)


class IsTemplateDomain(permissions.BasePermission):
    def __init__(self, *args, **kwargs):
        kwargs['domain'] = 'template'
        super().__init__(*args, **kwargs)
