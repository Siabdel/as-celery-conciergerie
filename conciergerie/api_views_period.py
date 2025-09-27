# conciergerie/api_views_period.py
from datetime import datetime, timedelta
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db.models import Q
from .models import Reservation, ServiceTask
from .serializers import ReservationSerializer, ServiceTaskSerializer


def _date_range(period: str, ref: datetime.date):
    """
    Retourne (start, end) selon la période demandée
    """
    if period == "day":
        start = ref
        end = ref + timedelta(days=1)
    elif period == "week":
        start = ref - timedelta(days=ref.weekday())  # lundi
        end = start + timedelta(days=7)
    elif period == "month":
        start = ref.replace(day=1)
        next_month = ref.replace(day=28) + timedelta(days=4)
        end = next_month.replace(day=1)
    else:
        raise ValueError("Période invalide – choix : day, week, month")
    return start, end


class ReservationPeriodAPIView(APIView):
    """
    GET /api/reservations/period/<day|week|month>/?date=YYYY-MM-DD
    date facultatif (defaut = today)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, period):
        date_str = request.query_params.get("date")
        ref = timezone.now().date() if not date_str else datetime.strptime(date_str, "%Y-%m-%d").date()
        try:
            start, end = _date_range(period, ref)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        qs = Reservation.objects.filter(
            check_in__gte=start,
            check_in__lt=end
        ).select_related("property")
        serializer = ReservationSerializer(qs, many=True)
        return Response({
            "period": period,
            "start": start,
            "end": end,
            "count": qs.count(),
            "results": serializer.data
        })


class ServiceTaskPeriodAPIView(APIView):
    """
    GET /api/tasks/period/<day|week|month>/?date=YYYY-MM-DD
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, period):
        date_str = request.query_params.get("date")
        ref = timezone.now().date() if not date_str else datetime.strptime(date_str, "%Y-%m-%d").date()
        try:
            start, end = _date_range(period, ref)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        qs = ServiceTask.objects.filter(
            start_date__gte=start,
            start_date__lt=end
        ).select_related("property", "employee")
        serializer = ServiceTaskSerializer(qs, many=True)
        return Response({
            "period": period,
            "start": start,
            "end": end,
            "count": qs.count(),
            "results": serializer.data
        })