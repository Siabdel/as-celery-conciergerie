
# conciergerie/property_public_views.py
from django.utils.dateparse import parse_date
from rest_framework.generics import RetrieveAPIView, ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Sum, Avg, Q
from django.utils import timezone

from conciergerie.models import Property, Reservation
from conciergerie.serializers import (
    PropertySerializer, ReservationSerializer
)
from core.models import ReservationStatus


# ---------- 1. full property object ----------
class PropertyDetailAPIView(RetrieveAPIView):
    """Toutes les infos + images + agent + amenities"""
    queryset = Property.objects.filter(is_active=True)
    serializer_class = PropertySerializer
    permission_classes = []          # public ou IsAuthenticated selon besoin


# ---------- 2. reservations for ONE property ----------
class ReservationByPropertyListAPIView(ListAPIView):
    serializer_class = ReservationSerializer
    pagination_class = None          # plus simple pour FullCalendar

    def get_queryset(self):
        qs = Reservation.objects.filter(
            property_id=self.kwargs["property_id"]
        ).exclude(
            reservation_status__in=[ReservationStatus.CANCELLED, ReservationStatus.EXPIRED]
        )
        # filtres optionnels
        start = self.request.query_params.get("start")
        end   = self.request.query_params.get("end")
        if start and end:
            qs = qs.filter(check_in__date__gte=start, check_out__date__lte=end)
        return qs.select_related("property")


# ---------- 3. revenue for ONE property ----------
class PropertyRevenueAPIView(APIView):
    def get(self, request, *args, **kwargs):
        start = request.query_params.get("start", str(timezone.now().date().replace(day=1)))
        end   = request.query_params.get("end", str(timezone.now().date()))
        revenue = (Reservation.objects.filter(
                property_id=kwargs["property_id"],
                check_in__date__gte=start,
                check_out__date__lte=end,
            ).exclude(reservation_status__in=[ReservationStatus.CANCELLED, ReservationStatus.EXPIRED])
            .aggregate(total=Sum("total_price"))["total"]
            or 0
        )
        return Response({"revenue": revenue, "currency": "EUR"})


# ---------- 4. occupancy for ONE property ----------
class PropertyOccupancyAPIView(APIView):
    def get(self, request, *args, **kwargs):
        start = parse_date(request.query_params.get("start", str(timezone.now().date().replace(day=1))))
        end   = parse_date(request.query_params.get("end", str(timezone.now().date())))
        nights = (end - start).days + 1
        occupied = (Reservation.objects.filter(
                property_id=kwargs["property_id"],
                check_in__date__lte=end,
                check_out__date__gte=start,
            ).exclude(reservation_status__in=[ReservationStatus.CANCELLED, ReservationStatus.EXPIRED])
            .aggregate(s=Sum("nights"))["s"]
            or 0
        )
        rate = occupied / nights * 100 if nights else 0
        return Response({"occupancy_rate": round(rate, 2)})