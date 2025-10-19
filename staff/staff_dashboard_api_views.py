# conciergerie/staff_dashboard_api_views.py
from django.utils.dateparse import parse_date
from django.utils import timezone
from django.db.models import Q, Count, Sum, Avg
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView

from staff.models import Employee, Absence
from conciergerie.models import ServiceTask, Reservation
from core.models import ReservationStatus
from staff.serializers import (
    EmployeeSerializer,
    AbsenceSerializer,
    ServiceTaskShortSerializer
)

# ---------- helpers ----------
def _agency_of_user(user):
    if user.is_superuser:
        return None
    if hasattr(user, 'employee'):
        return user.employee.agency
    first = user.properties_owned.first()
    return first.agency if first else None

def _agency_filter(qs, user):
    agency = _agency_of_user(user)
    return qs.filter(agency=agency) if agency else qs

# ---------- 1. Employees ----------
class EmployeeListAPIView(ListAPIView):
    serializer_class = EmployeeSerializer

    def get_queryset(self):
        return _agency_filter(Employee.objects.filter(is_active=True), self.request.user)

# ---------- 2. Absences ----------
class AbsenceListAPIView(ListAPIView):
    serializer_class = AbsenceSerializer

    def get_queryset(self):
        qs = _agency_filter(Absence.objects.all(), self.request.user)
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(type_absence=status_filter)
        return qs

class AbsenceUpdateAPIView(APIView):
    """PATCH /api/absences/<id>/  body: {type_absence: 'CONG'}"""
    def patch(self, request, pk):
        try:
            absence = _agency_filter(Absence.objects.all(), request.user).get(pk=pk)
        except Absence.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        new_type = request.data.get('type_absence')
        if new_type not in ['CONG', 'MALD', 'NJSU']:
            return Response({'error': 'Invalid type'}, status=status.HTTP_400_BAD_REQUEST)
        absence.type_absence = new_type
        absence.save()
        return Response(AbsenceSerializer(absence).data)

# ---------- 3. Tasks ----------
class TaskListAPIView(ListAPIView):
    serializer_class = ServiceTaskShortSerializer

    def get_queryset(self):
        qs = _agency_filter(ServiceTask.objects.all(), self.request.user)
        completed = self.request.query_params.get('completed')
        if completed is not None:
            qs = qs.filter(completed=completed.lower() == 'true')
        start = self.request.query_params.get('start')
        end   = self.request.query_params.get('end')
        if start and end:
            qs = qs.filter(start_date__gte=start, end_date__lte=end)
        return qs.select_related('property', 'employee', 'employee__user')

# ---------- 4. KPIs RH ----------
class StaffOccupancyKPIView(APIView):
    """Taux de présence du personnel aujourd'hui"""
    def get(self, request):
        today = timezone.now().date()
        total = _agency_filter(Employee.objects.filter(is_active=True), request.user).count()
        absent = _agency_filter(Absence.objects.filter(
            start_date__lte=today, end_date__gte=today, type_absence='CONG'
        ), request.user).values('employee').distinct().count()
        presence = 100 - (absent / total * 100) if total else 0
        return Response({'occupancy_rate': round(presence, 1)})

class TasksDelayKPIView(APIView):
    """Nombre de tâches en retard (non terminées et date passée)"""
    def get(self, request):
        now = timezone.now()
        qs = _agency_filter(ServiceTask.objects.filter(
            completed=False, end_date__lt=now
        ), request.user)
        return Response({'count': qs.count()})

class PendingLeavesKPIView(APIView):
    """Demandes en attente (type_absence = NJSU)"""
    def get(self, request):
        qs = _agency_filter(Absence.objects.filter(type_absence='NJSU'), request.user)
        return Response({'count': qs.count()})

class StaffCSATKPIView(APIView):
    """CSAT moyen des réservations liées à l’agence"""
    def get(self, request):
        qs = Reservation.objects.filter(
            agency=_agency_of_user(request.user),
            guest_rating__isnull=False
        ).aggregate(avg=Avg('guest_rating'))['avg']
        return Response({'csat': round(qs or 0, 1)})
