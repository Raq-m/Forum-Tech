from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsActiveAuthorOrReadOnly(BasePermission):
    """Lectura pública; escritura solo del autor autenticado y no suspendido."""

    def has_permission(self, request, view):
        return request.method in SAFE_METHODS or (
            request.user.is_authenticated and not request.user.is_suspended
        )

    def has_object_permission(self, request, view, obj):
        return request.method in SAFE_METHODS or obj.author_id == request.user.pk


class IsNotSuspended(BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS or (
            request.user.is_authenticated and not request.user.is_suspended
        )
