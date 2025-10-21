# core/admin_mixins.py
from django.contrib import admin

# core/admin_mixins.py
from django.contrib import admin

class BaseAgencyAdmin(admin.ModelAdmin):
    """
    Admin générique :
    - Cache les champs techniques
    - Définit automatiquement agency, created_by, updated_by
    - Restreint la vue aux objets de l’agence du user connecté
    """

    exclude = ("created_by", "updated_by", "agency")  # 👈 invisibles dans le formulaire
    readonly_fields = ("created_at", "updated_at")     # champs informatifs

    def save_model(self, request, obj, form, change):
        """
        Lors de l’enregistrement :
        - Définit automatiquement l’agence et les auteurs
        """
        if not obj.pk:
            obj.created_by = request.user
            obj.agency = getattr(request.user, "agency", None)
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        """
        Limite la visibilité à l’agence du user connecté
        """
        qs = super().get_queryset(request)
        user = request.user
        if user.is_superuser:
            return qs
        agency = getattr(user, "agency", None)
        return qs.filter(agency=agency) if agency else qs.none()

    def has_change_permission(self, request, obj=None):
        """
        Empêche un user de modifier un objet d’une autre agence.
        """
        if request.user.is_superuser or not obj:
            return True
        return obj.agency == getattr(request.user, "agency", None)

    def has_delete_permission(self, request, obj=None):
        """
        Même restriction pour la suppression.
        """
        if request.user.is_superuser or not obj:
            return True
        return obj.agency == getattr(request.user, "agency", None)


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
