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


class PropertyViewSet(viewsets.ModelViewSet):
    queryset = Property.objects.all()
    serializer_class = PropertySerializer
    permission_classes = [IsOwnerOrReadOnly]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["type", "owner__id"]
    search_fields = ["name", "address"]
    ordering_fields = ["price_per_night", "name"]

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


