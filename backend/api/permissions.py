from rest_framework.permissions import (SAFE_METHODS, BasePermission,
                                        IsAuthenticatedOrReadOnly)


class RecipePermission(IsAuthenticatedOrReadOnly):
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        if ((request.method in ('PATCH', 'DELETE')
                and obj.author == request.user)):
            return True
        if request.method in SAFE_METHODS:
            return True
        return False


class ReadOnly(BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS

    def has_object_permission(self, request, view, obj):
        return obj.author_id == request.user.id
