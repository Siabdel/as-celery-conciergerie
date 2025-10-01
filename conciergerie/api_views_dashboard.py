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
from datetime import datetime
from django.utils import timezone
import pandas as pd
from decimal import Decimal
from django.db import connection
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.db.models.functions import ExtractMonth

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
                .filter(check_in__lte=d, check_out__gt=d, reservation_status__in=[ResaStatus.CONFIRMED, ResaStatus.COMPLETED])
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

        

# ------------------------------------------------------------------
#  MOIS CIVIL COMPLET
# ------------------------------------------------------------------

# conciergerie/api_views_dashboard.py
from core.models import ResaStatus



# ------------------------------------------------------------------
#  STATUTS QUI COMPTENT POUR ACTIVITÉ + CA
# ------------------------------------------------------------------
ACTIVE_STATUSES = [
    ResaStatus.CONFIRMED,
    ResaStatus.IN_PROGRESS,
    ResaStatus.CHECKED_IN,
    ResaStatus.CHECKED_OUT,
    ResaStatus.COMPLETED,
]


def _agency_of(user):
    """Renvoie l’agence de l’utilisateur (owner ou employee) ou None."""
    if user.is_superuser:
        return None
    if hasattr(user, "employee"):
        return user.employee.agency
    # owner : agence de son premier bien
    first_prop = user.properties_owned.first()
    return first_prop.agency if first_prop else None


class DashboardMonthAPIView(APIView):
    """
    GET /api/dashboard/month/?day=YYYY-MM-DD
    Retourne les stats du **mois civil** contenant *day*.
    Filtre par agence de l’utilisateur connecté.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        day_str = request.query_params.get("day")
        ref = timezone.now().date() if not day_str else date.fromisoformat(day_str)

        # Bornes du mois civil
        # borne début de mois
        first = ref.replace(day=1)
        first_dt = timezone.make_aware(datetime(first.year, first.month, first.day))
        
        # borne fin de mois
        next_month = (first.replace(day=28) + timedelta(days=4)).replace(day=1)
        next_month_dt = timezone.make_aware(datetime(next_month.year, next_month.month, next_month.day))
        

        agency = _agency_of(request.user)
        if not agency and not request.user.is_superuser:
            return Response({"detail": "Votre compte n’est rattaché à aucune agence."}, status=status.HTTP_400_BAD_REQUEST)

        # ----------  STATS GLOBALES (mois)  ----------
        active_properties = Property.objects.for_user(request.user).filter(is_active=True).count()

        # ✅ uniquement les réservations qui COMPTENT (activité + CA)
        checkins_month = Reservation.objects.for_user(request.user).filter(
            check_in__gte=first_dt, check_in__lt=next_month_dt, reservation_status__in=ACTIVE_STATUSES
        ).count()
        checkouts_month = Reservation.objects.for_user(request.user).filter(
            check_out__gte=first_dt, check_out__lt=next_month_dt, reservation_status__in=ACTIVE_STATUSES
        ).count()
        services_todo_month = ServiceTask.objects.for_user(request.user).filter(
            start_date__gte=first_dt, start_date__lt=next_month_dt, completed=False
        ).count()

        # ----------  LISTES  ----------
        checkins = Reservation.objects.for_user(request.user).filter(
            check_in__gte=first_dt, check_in__lt=next_month_dt, reservation_status__in=ACTIVE_STATUSES
        ).select_related("property")[:150]
        checkouts = Reservation.objects.for_user(request.user).filter(
            check_out__gte=first_dt, check_out__lt=next_month_dt, reservation_status__in=ACTIVE_STATUSES
        ).select_related("property")[:150]
        services = ServiceTask.objects.for_user(request.user).filter(
            start_date__gte=first_dt, start_date__lt=next_month_dt
        ).select_related("property", "employee")[:150]

        # ----------  TAUX D’OCCUPATION (chaque jour du mois)  ----------
        occupancy = []
        for i in range((next_month - first).days):
            d = first + timedelta(days=i)

            d_start = timezone.make_aware(datetime(d.year, d.month, d.day))
            d_end   = timezone.make_aware(datetime(d.year, d.month, d.day, 23, 59, 59, 999999))

            total_props = Property.objects.for_user(request.user).count()
            booked = Reservation.objects.for_user(request.user).filter(
                check_in__lte=d_end, check_out__gt=d_start, reservation_status__in=ACTIVE_STATUSES
            ).count()
            rate = (booked / total_props * 100) if total_props else 0
            occupancy.append({"day": d, "rate": round(rate, 1)})

        # ----------  REVENU DU MOIS  ----------

        month_revenue = Reservation.objects.for_user(request.user).filter(
            check_in__gte=first_dt, check_in__lt=next_month_dt,
            reservation_status__in=ACTIVE_STATUSES
        ).aggregate(total=Sum("total_price"))["total"] or Decimal(0)

        return Response(
            {
                "agency": {"name": agency.name, "logo": agency.logo.url if agency.logo else "", "currency": agency.currency},
                "today_stats": {
                    "active_properties": active_properties,
                    "checkins": checkins_month,
                    "checkouts": checkouts_month,
                    "services_todo": services_todo_month,
                    "services_todo": services_todo_month,
                    "revenue": month_revenue,          # ← NOUVEAU
                },
                "checkins": CheckEventSerializer(checkins, many=True).data,
                "checkouts": CheckEventSerializer(checkouts, many=True).data,
                "services": ServiceEventSerializer(services, many=True).data,
                "occupancy_last7": OccupancySerializer(occupancy, many=True).data,
            }
        )

# ------------------------------------------------------------------
#  TRIMESTRE CIVIL COMPLET
# ------------------------------------------------------------------
# conciergerie/api_views_dashboard_pandas.py
# ------------------------------------------------------------------
#  STATUTS PERTINENTS (activité + CA)
# ------------------------------------------------------------------
ACTIVE_STATUSES = [
    ResaStatus.CONFIRMED,
    ResaStatus.IN_PROGRESS,
    ResaStatus.CHECKED_IN,
    ResaStatus.CHECKED_OUT,
    ResaStatus.COMPLETED,
]


def _agency_of(user):
    if user.is_superuser:
        return None
    if hasattr(user, "employee"):
        return user.employee.agency
    first_prop = user.properties_owned.first()
    return first_prop.agency if first_prop else None


class DashboardQuarterAPIView(APIView):
    """
    GET /api/dashboard/quarter/?day=YYYY-MM-DD
    Stats du **trimestre civil** (Q1, Q2, Q3, Q4) contenant *day*.
    Lecture SQL + pandas pour agrégations rapides.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        day_str = request.query_params.get("day")
        ref = timezone.now().date() if not day_str else date.fromisoformat(day_str)

        # Bornes du trimestre civil
        quarter = (ref.month - 1) // 3 + 1
        first_month = 3 * (quarter - 1) + 1
        first = date(ref.year, first_month, 1)
        next_quarter = date(ref.year + (1 if first_month == 10 else 0), (first_month + 3) % 12 or 12, 1)
        first_dt = timezone.make_aware(datetime(first.year, first.month, first.day))
        next_quarter_dt = timezone.make_aware(datetime(next_quarter.year, next_quarter.month, next_quarter.day))

        agency = _agency_of(request.user)
        if not agency and not request.user.is_superuser:
            return Response({"detail": "Votre compte n’est rattaché à aucune agence."}, status=status.HTTP_400_BAD_REQUEST)

        # ------------------------------------------------------------------
        #  1.  Récupération des IDs (petit volume) via ORM
        # ------------------------------------------------------------------
        agency = agency or Agency.objects.first()  # fallback super-user
        active_statuses = [s.value for s in ACTIVE_STATUSES]

        resa_ids = list(
            Reservation.objects.for_user(request.user)
            .filter(check_in__gte=first_dt, check_in__lt=next_quarter_dt, reservation_status__in=active_statuses)
            .values_list("id", flat=True)
        )
        task_ids = list(
            ServiceTask.objects.for_user(request.user)
            .filter(start_date__gte=first_dt, start_date__lt=next_quarter_dt, completed=False)
            .values_list("id", flat=True)
        )

        # ------------------------------------------------------------------
        #  2.  Lecture SQL brute + pandas (gros volume)
        # ------------------------------------------------------------------
        # ----------  Réservations  ----------
        if resa_ids:
            resa_sql = """
                SELECT r.id, r.check_in, r.check_out, r.total_price, r.platform, p.name AS property_name, r.guest_name, r.reservation_status
                FROM conciergerie_reservation r
                JOIN conciergerie_property p ON p.id = r.property_id
                WHERE r.id = ANY(%s)
            """
            resa_df = pd.read_sql(resa_sql, connection, params=[resa_ids])
            resa_df["check_in"] = pd.to_datetime(resa_df["check_in"])
            resa_df["check_out"] = pd.to_datetime(resa_df["check_out"])
            resa_df["nights"] = (resa_df["check_out"] - resa_df["check_in"]).dt.days
            resa_df["total_price"] = pd.to_numeric(resa_df["total_price"], errors="coerce")
            resa_df["rate"] = pd.to_numeric(resa_df["total_price"], errors="coerce") / resa_df["nights"].replace(0, 1)

            total_revenue = Decimal(resa_df["total_price"].sum())
            avg_price = Decimal(resa_df["rate"].mean())
            platform_breakdown = resa_df.groupby("platform")["total_price"].sum().to_dict()
            checkins_count = len(resa_df)
            checkouts_count = len(resa_df[resa_df["reservation_status"].isin(["CHECKED_OUT", "COMPLETED"])])
        else:
            total_revenue = avg_price = Decimal(0)
            platform_breakdown = {}
            checkins_count = checkouts_count = 0

        # ----------  Services  ----------
        if task_ids:
            task_sql = """
                SELECT t.id, t.start_date, t.type_service, t.status, p.name AS property_name, e.name AS employee_name
                FROM staff_servicetask t
                JOIN conciergerie_property p ON p.id = t.property_id
                JOIN staff_employee e ON e.id = t.employee_id
                WHERE t.id = ANY(%s)
            """
            task_df = pd.read_sql(task_sql, connection, params=[task_ids])
            task_df["start_date"] = pd.to_datetime(task_df["start_date"])
            services_count = len(task_df)
        else:
            services_count = 0

        # ----------  Taux d’occupation (chaque jour du trimestre)  ----------
        occupancy = []
        for i in range((next_quarter - first).days):
            d = first + timedelta(days=i)
            d_start = timezone.make_aware(datetime(d.year, d.month, d.day))
            d_end = timezone.make_aware(datetime(d.year, d.month, d.day, 23, 59, 59, 999999))
            total_props = Property.objects.for_user(request.user).count()
            booked = Reservation.objects.for_user(request.user).filter(
                check_in__lte=d_end, check_out__gt=d_start, reservation_status__in=ACTIVE_STATUSES
            ).count()
            rate = (booked / total_props * 100) if total_props else 0
            occupancy.append({"day": d, "rate": round(rate, 1)})

        # ------------------------------------------------------------------
        #  3.  Construction de la réponse (même structure que ORM)
        # ------------------------------------------------------------------
        agency = _agency_of(request.user)
        return Response(
            {
                "agency": {"name": agency.name, "logo": agency.logo.url if agency.logo else "", "currency": agency.currency},
                "today_stats": {
                    "active_properties": Property.objects.for_user(request.user).filter(is_active=True).count(),
                    "checkins": checkins_count,
                    "checkouts": checkouts_count,
                    "services_todo": services_count,
                    "revenue": str(total_revenue),
                    "avg_price": str(avg_price),
                    "platform_breakdown": platform_breakdown,
                },
                "checkins": CheckEventSerializer(
                    Reservation.objects.for_user(request.user).filter(
                        check_in__gte=first_dt, check_in__lt=next_quarter_dt, reservation_status__in=ACTIVE_STATUSES
                    ).select_related("property")[:200], many=True
                ).data,
                "checkouts": CheckEventSerializer(
                    Reservation.objects.for_user(request.user).filter(
                        check_out__gte=first_dt, check_out__lt=next_quarter_dt, reservation_status__in=ACTIVE_STATUSES
                    ).select_related("property")[:200], many=True
                ).data,
                "services": ServiceEventSerializer(
                    ServiceTask.objects.for_user(request.user).filter(
                        start_date__gte=first_dt, start_date__lt=next_quarter_dt
                    ).select_related("property", "employee")[:200], many=True
                ).data,
                "occupancy_last7": OccupancySerializer(occupancy, many=True).data,
            }
        )
        
        





class DashboardYearAPIView(APIView):
    """
    GET /api/dashboard/year/?year=2025
    Retourne les statistiques mensuelles pour une année donnée.
    """

    @method_decorator(cache_page(60 * 5))  # 5 min cache
    def get(self, request):
        year = int(request.query_params.get("year", datetime.now().year))

        # 1. Values-list brute : plus rapide que ORM
        qs = (
            Reservation.objects.filter(
                check_in__year=year,
                reservation_status__in=[
                    ResaStatus.CONFIRMED,
                    ResaStatus.CHECKED_IN,
                    ResaStatus.CHECKED_OUT,
                    ResaStatus.COMPLETED,
                ],
            )
            .annotate(month=ExtractMonth("check_in"))
            .values("month", "total_price", "cleaning_fee", "service_fee", "amount_paid")
        )

        # 2. DataFrame pandas
        df = pd.DataFrame.from_records(qs)

        if df.empty:
            return Response([])

        # 3. Agrégations par mois
        agg = (
            df.groupby("month")
            .agg(
                revenue=("total_price", "sum"),
                cleaning=("cleaning_fee", "sum"),
                service=("service_fee", "sum"),
                paid=("amount_paid", "sum"),
                nights=("month", "count"),  # nb résas
            )
            .reindex(range(1, 13), fill_value=0)  # complète les mois manquants
            .reset_index()
            .assign(month_name=lambda x: x["month"].apply(self._month_name))
        )

        # 4. Sérialisation
        return Response(agg.to_dict(orient="records"))

    # ---------------- helpers ----------------
    @staticmethod
    def _month_name(m):
        return datetime(1900, m, 1).strftime("%B")