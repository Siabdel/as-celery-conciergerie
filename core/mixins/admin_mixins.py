# core/admin_mixins.py
from django.contrib import admin

class AgencyScopedAdminMixin:
    """
    Mixin pour restreindre l'accès aux objets appartenant à la même agence
    que l'utilisateur connecté (sauf superadmin).
    À utiliser dans les classes ModelAdmin.
    """

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        user = request.user

        if user.is_superuser:
            return qs
        if hasattr(qs.model, "agency") and user.agency:
            return qs.filter(agency=user.agency)
        return qs.none()

    def save_model(self, request, obj, form, change):
        """
        Force l'association de l'agence de l'utilisateur connecté
        à tout nouvel objet créé.
        """
        if not obj.agency and hasattr(request.user, "agency"):
            obj.agency = request.user.agency
        obj.save()

    def has_change_permission(self, request, obj=None):
        """
        Un admin d'agence ne peut modifier que ses propres objets.
        """
        if request.user.is_superuser or obj is None:
            return True
        return hasattr(obj, "agency") and obj.agency == request.user.agency

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser or obj is None:
            return True
        return hasattr(obj, "agency") and obj.agency == request.user.agency
