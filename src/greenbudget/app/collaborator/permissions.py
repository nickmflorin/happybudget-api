from django.contrib.contenttypes.models import ContentType

from greenbudget.app import permissions

from .models import Collaborator


class BaseCollaboratorPermission(permissions.BasePermission):
    object_name = "budget"
    # Note: This message will almost never be used, as the ownership permission
    # will take priority over this one.  There is no way to know if a user is
    # not an owner of a Budget whether or not the user should not have permission
    # because they are not the owner or not a collaborator.
    message = "The user is not a collaborator for this {object_name}."
    user_dependency_flags = ['is_authenticated', 'is_active', 'is_verified']

    def __init__(self, object_name=None, **kwargs):
        self._object_name = object_name
        # If the access types are not explicitly provided, they will default
        # to the access types defined for the specific subclass permission.
        self._access_types = kwargs.get('access_types', None)
        super().__init__(**kwargs)

    def get_access_types(self, request):
        access_types = self._access_types
        if access_types is None and hasattr(self, 'access_types'):
            access_types = self.access_types
        if hasattr(access_types, '__call__'):
            access_types = access_types(request)

        if access_types is not None:
            assert isinstance(access_types, (list, tuple)) \
                and len(access_types) != 0, \
                "The provided access types must be an iterable with non-zero " \
                "length."
            Collaborator.ACCESS_TYPES.validate_values(access_types)
        return access_types

    def has_object_permission(self, request, view, obj):
        try:
            collaborator = Collaborator.objects.get(
                content_type=ContentType.objects.get_for_model(type(obj)),
                object_id=obj.pk,
                user=request.user
            )
        except Collaborator.DoesNotExist:
            return False
        else:
            access_types = self.get_access_types(request)
            if access_types and collaborator.access_type not in access_types:
                return (
                    "The user is a collaborator for this {object_name} but "
                    "does not have the correct access type."
                )
        return True


class IsCollaborator(BaseCollaboratorPermission):
    """
    Object level permission that ensures that the actively logged in user is
    a collaborator for the given object being accessed.
    """
    def access_types(self, request):
        if permissions.request_is_safe_method(request):
            return None
        return [
            Collaborator.ACCESS_TYPES.owner,
            Collaborator.ACCESS_TYPES.editor
        ]


class IsOwnerOrCollaborator(IsCollaborator):
    def has_object_permission(self, request, view, obj):
        assert hasattr(obj, 'user_owner'), \
            "The instance that is being collaborated on must dictate ownership."
        if not obj.is_owned_by(request.user):
            return super().has_object_permission(request, view, obj)
        return True


class IsOwnerOrCollaboratingOwner(IsOwnerOrCollaborator):
    access_types = [Collaborator.ACCESS_TYPES.owner]
