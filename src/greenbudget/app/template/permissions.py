from greenbudget.app import permissions
from greenbudget.app.budgeting.permissions import IsDomain


class IsTemplateDomain(IsDomain):
    def __init__(self, *args, **kwargs):
        kwargs['domain'] = 'template'
        super().__init__(*args, **kwargs)


class IsCommunityTemplate(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.community is True


class TemplateObjPermission(permissions.AND):
    """
    Dictates whether or not the logged in :obj:`User` is allowed access to
    a :obj:`Template` or any of it's related entities.
    """
    def __init__(self, **kwargs):
        object_name = kwargs.pop('object_name', 'budget')

        # When the permission is permissioning an object that is related to
        # the Budget, we must define how to obtain the original Budget based
        # on the related object.
        get_budget = kwargs.pop('get_budget', None)

        super().__init__(
            permissions.IsFullyAuthenticated(affects_after=True),
            permissions.OR(
                permissions.IsOwner(
                    get_permissioned_obj=get_budget,
                    object_name=object_name,
                ),
                permissions.AND(
                    IsCommunityTemplate(get_permissioned_obj=get_budget),
                    permissions.IsStaffUser
                )
            ),
            # View applicability isn't relevant for the mixins, since the mixins
            # are only applied to the nested object (i.e. object level
            # permissions) but view applicability is relevant for the central
            # view.
            is_view_applicable=False,
            **kwargs
        )
