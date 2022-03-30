from django.contrib.contenttypes.models import ContentType

from greenbudget.app import permissions

from .models import Collaborator


class IsCollaborator(permissions.BasePermission):
    """
    Object level permission that ensures that the actively logged in user is
    a collaborator for the given object being accessed.
    """
    object_name = "object"
    # Note: This message will almost never be used, as the ownership permission
    # will take priority over this one.  There is no way to know if a user is
    # not an owner of a Budget whether or not the user should not have permission
    # because they are not the owner or not a collaborator.
    message = "The user is not a collaborator for this {object_name}."
    user_dependency_flags = ['is_authenticated', 'is_active', 'is_verified']

    def __init__(self, object_name=None, **kwargs):
        self._object_name = object_name
        super().__init__(**kwargs)

    def has_object_permission(self, request, view, obj):
        try:
            collaborator = Collaborator.objects.get(
                content_type=ContentType.objects.get_for_model(type(obj)),
                object_id=obj.pk,
                user=request.user
            )
        except Collaborator.DoesNotExist:
            return False
        if permissions.request_is_safe_method(request):
            return True
        return collaborator.access_type in (
            Collaborator.ACCESS_TYPES.owner, Collaborator.ACCESS_TYPES.editor)
