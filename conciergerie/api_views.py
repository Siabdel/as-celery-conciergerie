from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from conciergerie.models import Property, Reservation, ServiceTask, Incident, AdditionalExpense
from staff.models import Employee
from core.models import UserProfile, Agency
from datetime import date, timedelta, datetime
from django.utils import timezone
from .serializers import (
    PropertySerializer, ReservationSerializer, ServiceTaskSerializer,
    IncidentSerializer, AdditionalExpenseSerializer, EmployeeSerializer
)
from .permissions import IsOwnerOrReadOnly, IsManagerOrReadOnly

# conciergerie/api_views_dashboard.py
from datetime import date, timedelta
from django.utils import timezone
from django.db.models import Count, Q
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from core.models import ResaStatus, TaskTypeService
from conciergerie.models import Reservation, ServiceTask, Property
from conciergerie.serializers import (
    CheckEventSerializer,
    ServiceEventSerializer,
    OccupancySerializer,
)

# conciergerie/views.py
from django.utils import timezone
from rest_framework.decorators import action
from core.models import ResaStatus


class PropertyViewSet(viewsets.ModelViewSet):
    queryset = Property.objects.all()
    serializer_class = PropertySerializer
    permission_classes = [IsOwnerOrReadOnly]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["type", "owner__id"]
    search_fields = ["name", "address"]
    ordering_fields = ["price_per_night", "name"]

    def get_queryset(self):
        # **filtrage par agence de l’utilisateur connecté**
        return Property.objects.for_user(self.request.user)

    # ------------------------------------------------------------------
    #  ✅ Disponibles uniquement
    # ------------------------------------------------------------------
    @action(detail=False, methods=['get'])
    def available(self, request):
        """Biens disponibles (is_active=True) de l’agence connectée."""
        qs = self.get_queryset().filter(is_active=True)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def myagency(self, request):
        """Biens de l’agence de l’utilisateur connecté."""
        queryset = self.get_queryset()  # déjà filtré par for_user()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=["get"])
    def revenue(self, request, pk=None):
        property = self.get_object()
        total_revenue = sum(r.total_price for r in property.reservations.all())
        return Response({"property": property.name, "revenue": total_revenue})

    @action(detail=True, methods=["get"])
    def occupancy(self, request, pk=None):
        property = self.get_object()
        total_days = sum(r.get_duration() for r in property.reservations.all())
        return Response({"property": property.name, "occupancy_days": total_days})



    @action(detail=False, methods=['get'])
    def available_for_period(self, request):
        """
        Biens **disponibles** (aucune réservation ACTIVE chevauchant la période).
        URL : /api/properties/available-for-period/?start=YYYY-MM-DD&end=YYYY-MM-DD
        """
        start_str = request.query_params.get("start")
        end_str = request.query_params.get("end")
        if not start_str or not end_str:
            return Response({"error": "Paramètres 'start' et 'end' requis."}, status=400)

        start = timezone.make_aware(datetime.fromisoformat(start_str))
        end = timezone.make_aware(datetime.fromisoformat(end_str))

        # ------------------------------------------------------------------
        #  1.  Réservations ACTIVES chevauchant la période
        # ------------------------------------------------------------------
        booked_property_ids = (
            Reservation.objects.for_user(request.user)
            .filter(
                reservation_status__in=[
                    ResaStatus.CONFIRMED,
                    ResaStatus.IN_PROGRESS,
                    ResaStatus.CHECKED_IN,
                    ResaStatus.CHECKED_OUT,
                ],
                # chevauche la période
                check_in__lt=end,
                check_out__gt=start,
            )
            .values_list("property_id", flat=True)
        )

        # ------------------------------------------------------------------
        #  2.  Biens NON réservés pendant la période
        # ------------------------------------------------------------------
        qs = self.get_queryset().exclude(id__in=booked_property_ids)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

class ReservationViewSet(viewsets.ModelViewSet):
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["property__id", "reservation_status", "platform"]
    search_fields = ["guest_name", "guest_email"]
    ordering_fields = ["check_in", "check_out", "total_price"]


class ServiceTaskViewSet(viewsets.ModelViewSet):
    queryset = ServiceTask.objects.all()
    serializer_class = ServiceTaskSerializer
    permission_classes = [IsManagerOrReadOnly]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["status", "employee__id", "property__id", "type_service"]
    search_fields = ["description"]
    ordering_fields = ["start_date", "end_date"]


class IncidentViewSet(viewsets.ModelViewSet):
    queryset = Incident.objects.all()
    serializer_class = IncidentSerializer

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["property__id", "status", "type"]
    search_fields = ["title", "description"]
    ordering_fields = ["date_reported", "status"]


class AdditionalExpenseViewSet(viewsets.ModelViewSet):
    queryset = AdditionalExpense.objects.all()
    serializer_class = AdditionalExpenseSerializer

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["property__id", "expense_type", "is_recurring"]
    ordering_fields = ["amount", "occurrence_date"]


class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["role", "is_active"]
    search_fields = ["name", "phone_number"]
    ordering_fields = ["hire_date", "name"]


