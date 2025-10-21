    
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from django.utils import timezone
from .models import Employee, Absence, Task, Reservation
from .serializers import EmployeeSerializer, AbsenceSerializer, TaskSerializer, ReservationSerializer

import pandas as pd
from core.api.permissions import IsAgencyAdminOrEmployee

""" 
Dans cette section, nous allons créer la logique pour vérifier si un employé est disponible à un moment 
donné en fonction de ses absences. Cela se fait au moment 
de l'assignation des tâches ou lors de la consultation des employés disponibles.
"""

# Viewset for Employee
class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    permission_classes = [IsAgencyAdminOrEmployee]

    # Get employees available today (not absent)
    @action(detail=False, methods=['get'])
    def available_today(self, request):
        today = timezone.now().date()

        # Get employees who are not absent today
        absent_employees = Absence.objects.filter(start_date__lte=today, end_date__gte=today).values_list('employee', flat=True)
        available_employees = Employee.objects.exclude(id__in=absent_employees)
        serializer = self.get_serializer(available_employees, many=True)
        return Response(serializer.data)

# Viewset for Absence
class AbsenceViewSet(viewsets.ModelViewSet):
    queryset = Absence.objects.all()
    serializer_class = AbsenceSerializer

# Viewset for Task
class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer

    # Check employee availability when assigning a task
    def create(self, request, *args, **kwargs):
        employee_id = request.data['employee']
        start_time = pd.to_datetime(request.data['start_time'])
        end_time = pd.to_datetime(request.data['end_time'])

        # Check if employee is absent during this period
        absences = Absence.objects.filter(
            employee__id=employee_id,
            start_date__lte=start_time.date(),
            end_date__gte=end_time.date()
        )

        if absences.exists():
            return Response({"error": "Employee is absent during this period."}, status=400)

        return super().create(request, *args, **kwargs)

# Viewset for Reservations
class ReservationViewSet(viewsets.ModelViewSet):
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer
