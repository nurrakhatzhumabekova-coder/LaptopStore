from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    """
    Разрешение: только владелец объекта может его изменять/удалять
    """

    def has_object_permission(self, request, view, obj):
        # Проверяем, есть ли у объекта поле user
        if hasattr(obj, 'user'):
            return obj.user == request.user

        # Если поле называется author
        if hasattr(obj, 'author'):
            return obj.author == request.user

        return False


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Разрешение: только владелец может изменять, но все могут читать
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        if hasattr(obj, 'user'):
            return obj.user == request.user

        return False


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Разрешение: только админ может изменять, все могут читать
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_staff


class IsAuthenticatedAndVerified(permissions.BasePermission):
    """
    Разрешение: пользователь должен быть авторизован и верифицирован
    """

    def has_permission(self, request, view):
        return (request.user and
                request.user.is_authenticated and
                request.user.is_verified)