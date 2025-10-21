
# core/api/views.py
from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from core.models import LandingSection
from core.api.serializers import LandingSectionSerializer

class LandingSectionPublicViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API publique — renvoie les sections actives de la landing page.
    Pas d'authentification requise.
    """
    serializer_class = LandingSectionSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return LandingSection.objects.filter(is_active=True).order_by("order")
