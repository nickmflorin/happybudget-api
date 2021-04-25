from rest_framework import permissions


class CommunityTemplatePermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        permission = permissions.IsAdminUser()
        if obj.community is True:
            return permission.has_permission(request, view)
        return obj.created_by == request.user
