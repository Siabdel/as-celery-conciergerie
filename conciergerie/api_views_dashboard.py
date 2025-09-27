# conciergerie/api_views_dashboard.py
from datetime import date, timedelta
from django.utils import timezone
from django.db.models import Count, Q, Sum, F
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
from staff.models import Employee


def _week_boundaries(wk: date):
    """Renvoie (lundi, dimanche+1) de la semaine contenant *wk*."""
    monday = wk - timedelta(days=wk.weekday())          # 0 = lundi
    sunday = monday + timedelta(days=7)                 # exclu
    return monday, sunday



def _week_boundaries(wk: date):
    """Renvoie (lundi, dimanche+1) de la semaine contenant *wk*."""
    monday = wk - timedelta(days=wk.weekday())          # 0 = lundi
    sunday = monday + timedelta(days=7)                 # exclu
    return monday, sunday


def _agency_of(user):
    """Renvoie l’agence de l’utilisateur (owner ou staff)."""
    if hasattr(user, "employee"):
        return user.employee.agency
    # owner : on prend l’agence de son **premier** bien (tous ses biens sont dans la même agence)
    if user.properties_owned.exists():
        return user.properties_owned.first().agency
    return None


class DashboardAPIView(APIView):
    """
    GET /api/dashboard/?day=YYYY-MM-DD
    Semaine complète (lundi → dimanche) de *day*.
    Filtré par l’agence de l’utilisateur connecté.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        day_str = request.query_params.get("day")
        ref = timezone.now().date() if not day_str else date.fromisoformat(day_str)
        monday, sunday = _week_boundaries(ref)

        agency = _agency_of(request.user)
        if not agency:
            return Response({"detail": "Aucune agence rattachée à cet utilisateur."}, status=400)

        # ----------  STATS GLOBALES (semaine)  ----------
        active_properties = Property.objects.for_user(request.user).filter(is_active=True).count()

        checkins_week = (
            Reservation.objects.for_user(request.user)
            .filter(check_in__date__gte=monday, check_in__date__lt=sunday)
            .count()
        )
        checkouts_week = (
            Reservation.objects.for_user(request.user)
            .filter(check_out__date__gte=monday, check_out__date__lt=sunday)
            .count()
        )
        services_todo_week = (
            ServiceTask.objects.for_user(request.user)
            .filter(start_date__date__gte=monday, start_date__date__lt=sunday, completed=False)
            .count()
        )

        # ----------  LISTES (événements de la semaine)  ----------
        checkins = (
            Reservation.objects.for_user(request.user)
            .filter(check_in__date__gte=monday, check_in__date__lt=sunday)
            .select_related("property")[:50]
        )
        checkouts = (
            Reservation.objects.for_user(request.user)
            .filter(check_out__date__gte=monday, check_out__date__lt=sunday)
            .select_related("property")[:50]
        )
        services = (
            ServiceTask.objects.for_user(request.user)
            .filter(start_date__date__gte=monday, start_date__date__lt=sunday)
            .select_related("property", "employee")[:50]
        )

        # ----------  TAUX OCCUPATION 7 DERNIERS JOURS  ----------
        occupancy = []
        for i in range(7):
            d = monday + timedelta(days=i)
            total_props = Property.objects.for_user(request.user).count()
            booked = (
                Reservation.objects.for_user(request.user)
                .filter(check_in__lte=d, check_out__gt=d, reservation_status__in=[ResaStatus.CONFIRMED, ResaStatus.CHECKED_IN])
                .count()
            )
            rate = (booked / total_props * 100) if total_props else 0
            occupancy.append({"day": d, "rate": round(rate, 1)})

        # ----------  REPONSE  ----------
        return Response(
            {
                "agency": {"name": agency.name, "logo": agency.logo.url if agency.logo else "", "currency": agency.currency},
                "today_stats": {  # clé inchangée pour Vue
                    "active_properties": active_properties,
                    "checkins": checkins_week,
                    "checkouts": checkouts_week,
                    "services_todo": services_todo_week,
                },
                "checkins": CheckEventSerializer(checkins, many=True).data,
                "checkouts": CheckEventSerializer(checkouts, many=True).data,
                "services": ServiceEventSerializer(services, many=True).data,
                "occupancy_last7": OccupancySerializer(occupancy, many=True).data,
            }
        )


def _week_boundaries(wk: date):
    """Renvoie (lundi, dimanche+1) de la semaine contenant *wk*."""
    monday = wk - timedelta(days=wk.weekday())          # 0 = lundi
    sunday = monday + timedelta(days=7)                 # exclu
    return monday, sunday


class DashboardWeekAPIView(APIView):
    """
    GET /api/dashboard/?day=YYYY-MM-DD
    Si *day* absent → semaine en cours.
    Toutes les statistiques sont calculées sur la **semaine** de *day*.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        day_str = request.query_params.get("day")
        ref = timezone.now().date() if not day_str else date.fromisoformat(day_str)
        monday, sunday = _week_boundaries(ref)

        agency = request.user.profile.agency

        # ----------  STATS GLOBALES (semaine)  ----------
        active_properties = Property.objects.for_user(request.user).filter(is_active=True).count()

        checkins_week = (
            Reservation.objects.for_user(request.user)
            .filter(check_in__date__gte=monday, check_in__date__lt=sunday, reservation_status=ResaStatus.PENDING)
            .count()
        )
        checkouts_week = (
            Reservation.objects.for_user(request.user)
            .filter(check_out__date__gte=monday, check_out__date__lt=sunday, reservation_status=ResaStatus.CHECKED_IN)
            .count()
        )
        services_todo_week = (
            ServiceTask.objects.for_user(request.user)
            .filter(start_date__date__gte=monday, start_date__date__lt=sunday, completed=False)
            .count()
        )

        # ----------  LISTES (événements de la semaine)  ----------
        checkins = (
            Reservation.objects.for_user(request.user)
            .filter(check_in__date__gte=monday, check_in__date__lt=sunday)
            .select_related("property")[:50]
        )
        checkouts = (
            Reservation.objects.for_user(request.user)
            .filter(check_out__date__gte=monday, check_out__date__lt=sunday)
            .select_related("property")[:50]
        )
        services = (
            ServiceTask.objects.for_user(request.user)
            .filter(start_date__date__gte=monday, start_date__date__lt=sunday)
            .select_related("property", "employee")[:50]
        )

        # ----------  TAUX OCCUPATION 7 DERNIERS JOURS  ----------
        occupancy = []
        for i in range(7):
            d = monday + timedelta(days=i)
            total_props = Property.objects.for_user(request.user).count()
            booked = (
                Reservation.objects.for_user(request.user)
                .filter(check_in__lte=d, check_out__gt=d, reservation_status__in=[ResaStatus.CONFIRMED, ResaStatus.CHECKED_IN])
                .count()
            )
            rate = (booked / total_props * 100) if total_props else 0
            occupancy.append({"day": d, "rate": round(rate, 1)})

        # ----------  RESPONSE  ----------
        return Response(
            {
                "agency": {"name": agency.name, "logo": agency.logo.url if agency.logo else "", "currency": agency.currency},
                "today_stats": {  # clé inchangée pour Vue
                    "active_properties": active_properties,
                    "checkins": checkins_week,
                    "checkouts": checkouts_week,
                    "services_todo": services_todo_week,
                },
                "checkins": CheckEventSerializer(checkins, many=True).data,
                "checkouts": CheckEventSerializer(checkouts, many=True).data,
                "services": ServiceEventSerializer(services, many=True).data,
                "occupancy_last7": OccupancySerializer(occupancy, many=True).data,
            }
        )