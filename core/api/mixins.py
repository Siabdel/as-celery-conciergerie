# core/api/mixins.py
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from core.api.permissions import IsSameAgency


class AgencyScopedViewSetMixin(viewsets.ModelViewSet):
    """
    ViewSet de base pour tous les modèles multi-tenant (héritant d’AbstractTenantModel).
    Filtre automatiquement par agence et rattache l’agence du user à la création.
    """
    permission_classes = [IsAuthenticated, IsSameAgency]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.is_superuser:
            return qs
        if hasattr(qs.model, "agency") and user.agency:
            return qs.filter(agency=user.agency)
        return qs.none()

    def perform_create(self, serializer):
        user = self.request.user
        if hasattr(serializer.Meta.model, "agency") and user.agency:
            serializer.save(agency=user.agency, created_by=user)
        else:
            serializer.save(created_by=user)
