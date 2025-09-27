from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsOwnerOrReadOnly(BasePermission):
    """
    Seul le propriétaire peut modifier un bien, 
    les autres peuvent juste lire.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return getattr(obj, "owner", None) == request.user


class IsManagerOrReadOnly(BasePermission):
    """
    Seuls les managers/employés peuvent modifier les tâches.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        if hasattr(request.user, "employee"):
            return request.user.employee.role in ["manager", "concierge"]
        return False


# conciergerie/permissions.py
class IsAgencyMember(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return hasattr(user, "employee") or user.properties_owned.exists()