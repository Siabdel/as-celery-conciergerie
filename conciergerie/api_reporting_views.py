
# conciergerie/reporting_views.py
from django.db.models import (
    Count, Sum, Avg, F, Q, FloatField, ExpressionWrapper, DurationField, Min
)
from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from datetime import timedelta
from decimal import Decimal

from conciergerie.models import (
    Property, Reservation, AdditionalExpense, Incident, Employee, ServiceTask
)
from core.models import ReservationStatus
# conciergerie/views.py
from rest_framework.generics import ListAPIView
from conciergerie.models import Reservation
from conciergerie.serializers import ReservationSerializer
from core.models import ReservationStatus



# --------------------------------------------------
# Helper : récupère l'agence de l'utilisateur connecté
# --------------------------------------------------
def _agency_of(user):
    """
    Retourne l'agence de l'utilisateur connecté.
    Si super-utilisateur -> None (pas de filtre)
    """
    if user.is_superuser:
        return None
    if hasattr(user, "employee") and user.employee:
        return user.employee.agency
    first_prop = user.properties_owned.first()
    return first_prop.agency if first_prop else None


# --------------------------------------------------
# Filtre par agence si besoin
# --------------------------------------------------
def _filter_by_agency(queryset, user):
    agency = _agency_of(user)
    if agency:
        return queryset.filter(agency=agency)
    return queryset

#-----------------------
#- les resa aujourdhui 
#--------------------------
class TodayCheckinsView(ListAPIView):
    serializer_class = ReservationSerializer
    pagination_class = None

    def get_queryset(self):
        today = timezone.now().date()
        return (
            Reservation.objects.filter(
                agency=self.request.user.employee.agency,
                check_in__date=today,
                reservation_status=ReservationStatus.CONFIRMED
            )
            .select_related("property", )
            .order_by("check_in")
        )
# --------------------------------------------------
# 1. Available Apartments
# --------------------------------------------------
class AvailableApartmentsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        date = parse_date(request.query_params.get("date", str(timezone.now().date())))
        occupied_ids = (
            _filter_by_agency(Reservation.objects, request.user)
            .filter(
                check_in__date__lte=date,
                check_out__date__gt=date
            )
            .exclude(reservation_status__in=[ReservationStatus.CANCELLED, ReservationStatus.EXPIRED])
            .values_list("property_id", flat=True)
        )
        free = _filter_by_agency(Property.objects, request.user).filter(
            is_active=True
        ).exclude(id__in=occupied_ids)
        return Response({"available_count": free.count(), "date": date})


# --------------------------------------------------
# 2. Vacancy Rate
# --------------------------------------------------
class VacancyRateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        start, end = request.query_params.get("start"), request.query_params.get("end")
        if not (start and end):
            return Response({"error": "start & end required"}, status=400)

        start_date = parse_date(start)
        end_date = parse_date(end)
        total_nights = (
            _filter_by_agency(Property.objects, request.user).filter(is_active=True).count()
            * (end_date - start_date).days
        )
        occupied_nights = (
            _filter_by_agency(Reservation.objects, request.user)
            .filter(
                check_in__date__gte=start,
                check_out__date__lte=end,
            )
            .exclude(reservation_status__in=[ReservationStatus.CANCELLED, ReservationStatus.EXPIRED])
            .aggregate(
                s=Sum(
                    ExpressionWrapper(
                        F("check_out") - F("check_in"), output_field=DurationField()
                    )
                )
            )["s"]
        )
        occupied_nights = occupied_nights.days if occupied_nights else 0
        vacancy_rate = (total_nights - occupied_nights) / total_nights * 100 if total_nights else 0
        return Response({"vacancy_rate_%": round(vacancy_rate, 2)})


# --------------------------------------------------
# 3. Occupancy Rate
# --------------------------------------------------
class OccupancyRateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        start, end = request.query_params.get("start"), request.query_params.get("end")
        if not (start and end):
            return Response({"error": "start & end required"}, status=400)

        start_date = parse_date(start)
        end_date = parse_date(end)
        total_nights = (
            _filter_by_agency(Property.objects, request.user).filter(is_active=True).count()
            * (end_date - start_date).days
        )
        occupied_nights = (
            _filter_by_agency(Reservation.objects, request.user)
            .filter(
                check_in__date__gte=start,
                check_out__date__lte=end,
            )
            .exclude(reservation_status__in=[ReservationStatus.CANCELLED, ReservationStatus.EXPIRED])
            .aggregate(
                s=Sum(
                    ExpressionWrapper(
                        F("check_out") - F("check_in"), output_field=DurationField()
                    )
                )
            )["s"]
        )
        occupied_nights = occupied_nights.days if occupied_nights else 0
        occupancy_rate = occupied_nights / total_nights * 100 if total_nights else 0
        return Response({"occupancy_rate_%": round(occupancy_rate, 2)})


# --------------------------------------------------
# 4. Active Bookings
# --------------------------------------------------
class ActiveBookingsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        now = timezone.now()
        qs = (
            _filter_by_agency(Reservation.objects, request.user)
            .filter(check_out__gte=now)
            .exclude(reservation_status__in=[ReservationStatus.CANCELLED, ReservationStatus.EXPIRED])
            .count()
        )
        return Response({"active_bookings": qs})


# --------------------------------------------------
# 5. RevPAR
# --------------------------------------------------
class RevPARAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        start, end = request.query_params.get("start"), request.query_params.get("end")
        if not (start and end):
            return Response({"error": "start & end required"}, status=400)

        start_date = parse_date(start)
        end_date = parse_date(end)
        total_nights = (
            _filter_by_agency(Property.objects, request.user).filter(is_active=True).count()
            * (end_date - start_date).days
        )
        revenue = (
            _filter_by_agency(Reservation.objects, request.user)
            .filter(
                check_in__date__gte=start,
                check_out__date__lte=end,
            )
            .exclude(reservation_status__in=[ReservationStatus.CANCELLED, ReservationStatus.EXPIRED])
            .aggregate(total=Sum("total_price"))["total"]
            or 0
        )
        revpar = float(revenue) / total_nights if total_nights else 0
        return Response({"revpar": round(revpar, 2), "currency": "EUR"})


# --------------------------------------------------
# 6. Avg Basket
# --------------------------------------------------
class AvgBasketAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        start, end = request.query_params.get("start"), request.query_params.get("end")
        if not (start and end):
            return Response({"error": "start & end required"}, status=400)

        revenue, count = (
            _filter_by_agency(Reservation.objects, request.user)
            .filter(
                check_in__date__gte=start,
                check_out__date__lte=end,
            )
            .exclude(reservation_status__in=[ReservationStatus.CANCELLED, ReservationStatus.EXPIRED])
            .aggregate(
                revenue=Sum("total_price", default=0),
                count=Count("id")
            )
            .values()
        )
        avg_basket = float(revenue) / count if count else 0
        return Response({"avg_basket": round(avg_basket, 2), "currency": "EUR"})


# --------------------------------------------------
# 7. Gross Margin
# --------------------------------------------------
class GrossMarginAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        start, end = request.query_params.get("start"), request.query_params.get("end")
        if not (start and end):
            return Response({"error": "start & end required"}, status=400)

        revenue = (
            _filter_by_agency(Reservation.objects, request.user)
            .filter(
                check_in__date__gte=start,
                check_out__date__lte=end,
            )
            .exclude(reservation_status__in=[ReservationStatus.CANCELLED, ReservationStatus.EXPIRED])
            .aggregate(total=Sum("total_price"))["total"]
            or 0
        )
        costs = (
            _filter_by_agency(AdditionalExpense.objects, request.user)
            .filter(
                occurrence_date__gte=start,
                occurrence_date__lte=end,
            ).aggregate(total=Sum("amount"))["total"]
            or 0
        )
        margin = (float(revenue) - float(costs)) / float(revenue) * 100 if revenue else 0
        return Response({"gross_margin_%": round(margin, 2)})


# --------------------------------------------------
# 8. Loyalty Rate
# --------------------------------------------------
class LoyaltyRateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        start, end = request.query_params.get("start"), request.query_params.get("end")
        if not (start and end):
            return Response({"error": "start & end required"}, status=400)

        all_guests = list(
            _filter_by_agency(Reservation.objects, request.user)
            .filter(
                check_in__date__gte=start,
                check_out__date__lte=end,
            )
            .exclude(reservation_status__in=[ReservationStatus.CANCELLED, ReservationStatus.EXPIRED])
            .values_list("guest_email", flat=True)
            .distinct()
        )
        repeat_guests = (
            _filter_by_agency(Reservation.objects, request.user)
            .filter(guest_email__in=all_guests)
            .values("guest_email")
            .annotate(c=Count("id"))
            .filter(c__gt=1)
            .count()
        )
        loyalty_rate = repeat_guests / len(all_guests) * 100 if all_guests else 0
        return Response({"loyalty_rate_%": round(loyalty_rate, 2)})


# --------------------------------------------------
# 9. CSAT
# --------------------------------------------------
class CSATAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        start, end = request.query_params.get("start"), request.query_params.get("end")
        if not (start and end):
            return Response({"error": "start & end required"}, status=400)

        avg_rating = (
            _filter_by_agency(Reservation.objects, request.user)
            .filter(
                check_in__date__gte=start,
                check_out__date__lte=end,
                guest_rating__isnull=False,
            )
            .exclude(reservation_status__in=[ReservationStatus.CANCELLED, ReservationStatus.EXPIRED])
            .aggregate(avg=Avg("guest_rating"))["avg"]
        )
        return Response({"csat": round(avg_rating or 0, 2)})


# --------------------------------------------------
# 10. Avg Service Cost
# --------------------------------------------------
class AvgServiceCostAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        start, end = request.query_params.get("start"), request.query_params.get("end")
        if not (start and end):
            return Response({"error": "start & end required"}, status=400)

        costs = (
            _filter_by_agency(AdditionalExpense.objects, request.user)
            .filter(
                occurrence_date__gte=start,
                occurrence_date__lte=end,
            ).aggregate(total=Sum("amount"))["total"]
            or 0
        )
        tasks = (
            _filter_by_agency(ServiceTask.objects, request.user)
            .filter(
                start_date__gte=start,
                end_date__lte=end,
            ).count()
        )
        avg_cost = float(costs) / tasks if tasks else 0
        return Response({"avg_service_cost": round(avg_cost, 2), "currency": "EUR"})


# --------------------------------------------------
# 11. Portfolio Size
# --------------------------------------------------
class PortfolioSizeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        count = _filter_by_agency(Property.objects, request.user).filter(is_active=True).count()
        return Response({"portfolio_size": count})


# --------------------------------------------------
# 12. Avg Stay Duration
# --------------------------------------------------
class AvgStayDurationAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        start, end = request.query_params.get("start"), request.query_params.get("end")
        if not (start and end):
            return Response({"error": "start & end required"}, status=400)

        avg_nights = (
            _filter_by_agency(Reservation.objects, request.user)
            .filter(
                check_in__date__gte=start,
                check_out__date__lte=end,
            )
            .exclude(reservation_status__in=[ReservationStatus.CANCELLED, ReservationStatus.EXPIRED])
            .aggregate(avg=Avg("nights"))["avg"]
        )
        return Response({"avg_stay_nights": round(avg_nights or 0, 2)})


# --------------------------------------------------
# 13. Acceptance Rate
# --------------------------------------------------
class AcceptanceRateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        start, end = request.query_params.get("start"), request.query_params.get("end")
        if not (start and end):
            return Response({"error": "start & end required"}, status=400)

        total = _filter_by_agency(ServiceTask.objects, request.user).filter(
            start_date__gte=start, end_date__lte=end
        ).count()
        completed = _filter_by_agency(ServiceTask.objects, request.user).filter(
            start_date__gte=start,
            end_date__lte=end,
            completed=True,
        ).count()
        rate = completed / total * 100 if total else 0
        return Response({"acceptance_rate_%": round(rate, 2)})


# --------------------------------------------------
# 14. CLV
# --------------------------------------------------
class CLVAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        start, end = request.query_params.get("start"), request.query_params.get("end")
        if not (start and end):
            return Response({"error": "start & end required"}, status=400)

        clv = (
            _filter_by_agency(Reservation.objects, request.user)
            .filter(
                check_in__date__gte=start,
                check_out__date__lte=end,
            )
            .exclude(reservation_status__in=[ReservationStatus.CANCELLED, ReservationStatus.EXPIRED])
            .values("guest_email")
            .annotate(clv=Sum("total_price"))
            .aggregate(avg=Avg("clv"))["avg"]
        )
        return Response({"avg_clv": round(clv or 0, 2), "currency": "EUR"})


# --------------------------------------------------
# 15. CAC
# --------------------------------------------------
class CACAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        start, end = request.query_params.get("start"), request.query_params.get("end")
        if not (start and end):
            return Response({"error": "start & end required"}, status=400)

        marketing_costs = (
            _filter_by_agency(AdditionalExpense.objects, request.user)
            .filter(
                expense_type="other",  # suppose marketing in « other »
                occurrence_date__gte=start,
                occurrence_date__lte=end,
            ).aggregate(total=Sum("amount"))["total"]
            or 0
        )
        all_guests = list(
            _filter_by_agency(Reservation.objects, request.user)
            .filter(
                check_in__date__gte=start,
                check_out__date__lte=end,
            )
            .exclude(reservation_status__in=[ReservationStatus.CANCELLED, ReservationStatus.EXPIRED])
            .values_list("guest_email", flat=True)
            .distinct()
        )
        new_guests = (
            _filter_by_agency(Reservation.objects, request.user)
            .filter(guest_email__in=all_guests)
            .values("guest_email")
            .annotate(min_checkin=Min("check_in"))
            .filter(min_checkin__gte=parse_date(start))
            .count()
        )
        cac = float(marketing_costs) / new_guests if new_guests else 0
        return Response({"cac": round(cac, 2), "currency": "EUR"})