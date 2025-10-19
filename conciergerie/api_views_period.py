# conciergerie/api_views_period.py
from datetime import datetime, timedelta, date
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db.models import Q
from .models import Reservation, ServiceTask
from .serializers import ReservationSerializer, ServiceTaskSerializer

from django.db.models import Count, Q
from rest_framework import status
from core.models import ReservationStatus
from staff.models import Employee


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

# conciergerie/api_views_period.py


def _week_boundaries(wk: date):
    monday = wk - timedelta(days=wk.weekday())
    sunday = monday + timedelta(days=7)
    return monday, sunday


def _agency_of(user):
    """Renvoie l’agence de l’utilisateur (owner ou employee) ou None."""
    if user.is_superuser:
        return None
    if hasattr(user, "employee"):
        return user.employee.agency
    # owner : agence de son premier bien
    first_prop = user.properties_owned.first()
    return first_prop.agency if first_prop else None


class ReservationPeriodAPIView(APIView):
    """
    GET /api/reservations/period/<day|week|month>/?day=YYYY-MM-DD
    Semaine complète (lundi → dimanche) de *day*.
    Filtre par agence de l’utilisateur connecté.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, period):
        day_str = request.query_params.get("day")
        ref = timezone.now().date() if not day_str else date.fromisoformat(day_str)
        monday, sunday = _week_boundaries(ref)

        agency = _agency_of(request.user)
        if not agency and not request.user.is_superuser:
            return Response({"detail": "Votre compte n’est rattaché à aucune agence."}, status=status.HTTP_400_BAD_REQUEST)

        # Bornes datetime aware
        monday_dt = timezone.make_aware(monday.timetuple()[:6])
        sunday_dt = timezone.make_aware(sunday.timetuple()[:6])

        qs = Reservation.objects.for_user(request.user).filter(
            check_in__gte=monday_dt,
            check_in__lt=sunday_dt,
        ).select_related("property")

        if period == "checkins":
            qs = qs.filter(check_in__gte=monday_dt, check_in__lt=sunday_dt)
        elif period == "checkouts":
            qs = qs.filter(check_out__gte=monday_dt, check_out__lt=sunday_dt)
        # on peut ajouter "confirmed", "pending", etc.

        serializer = CheckEventSerializer(qs, many=True)
        return Response(
            {
                "period": period,
                "start": monday,
                "end": sunday - timedelta(days=1),
                "count": qs.count(),
                "results": serializer.data,
            }
        )


class ServiceTaskPeriodAPIView(APIView):
    """
    GET /api/tasks/period/<day|week|month>/?day=YYYY-MM-DD
    Filtre par agence de l’utilisateur connecté.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, period):
        day_str = request.query_params.get("day")
        ref = timezone.now().date() if not day_str else date.fromisoformat(day_str)
        monday, sunday = _week_boundaries(ref)

        agency = _agency_of(request.user)
        if not agency and not request.user.is_superuser:
            return Response({"detail": "Votre compte n’est rattaché à aucune agence."}, status=status.HTTP_400_BAD_REQUEST)

        monday_dt = timezone.make_aware(monday.timetuple()[:6])
        sunday_dt = timezone.make_aware(sunday.timetuple()[:6])

        qs = ServiceTask.objects.for_user(request.user).filter(
            start_date__gte=monday_dt,
            start_date__lt=sunday_dt,
        ).select_related("property", "employee")

        if period == "todo":
            qs = qs.filter(completed=False)
        # on peut ajouter "completed", "cleaning", etc.

        serializer = ServiceEventSerializer(qs, many=True)
        return Response(
            {
                "period": period,
                "start": monday,
                "end": sunday - timedelta(days=1),
                "count": qs.count(),
                "results": serializer.data,
            }
        )