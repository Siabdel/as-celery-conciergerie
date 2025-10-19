from rest_framework import permissions
from core.models import CustomUser

class IsAgencyAdmin(permissions.BasePermission):
    """Autorise uniquement les administrateurs d’agence."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.role == CustomUser.Roles.AGENCY_ADMIN)


class IsEmployee(permissions.BasePermission):
    """Autorise uniquement les employés."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.role == CustomUser.Roles.EMPLOYEE)


class IsOwner(permissions.BasePermission):
    """Autorise uniquement les propriétaires."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.role == CustomUser.Roles.OWNER)


class IsSameAgency(permissions.BasePermission):
    """Autorise si l’utilisateur appartient à la même agence que la ressource consultée."""
    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        return hasattr(obj, "agency") and obj.agency == request.user.agency

class IsAgencyAdminOrEmployee(permissions.BasePermission):
    """Autorise les employés et les admins de l’agence."""
    def has_permission(self, request, view):
        return request.user.role in [
            CustomUser.Roles.AGENCY_ADMIN,
            CustomUser.Roles.EMPLOYEE
        ]
