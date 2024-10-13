
from datetime import datetime, timedelta
from schedule.models import Calendar, Event
from services_menage import serializers 
from django.utils.dateparse import parse_datetime
from django.http import JsonResponse
from django_celery_beat.models import PeriodicTask
from .serializers import PeriodicTaskSerializer
# DRF api rest
from rest_framework import viewsets, permissions, generics
from rest_framework.response import Response
from rest_framework.decorators import api_view
## 
from services_menage.models import Employee, Reservation, ServiceTask
from services_menage.serializers import TaskSerializer
from django.utils.dateparse import parse_date

class PeriodicTaskListCreate(generics.ListCreateAPIView):
    queryset = PeriodicTask.objects.all()
    serializer_class = PeriodicTaskSerializer



class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.all()
    serializer_class = serializers.EmployeeSerializer

class ReservationViewSet(viewsets.ModelViewSet):
    queryset = Reservation.objects.all()
    serializer_class = serializers.ReservationSerializer

class ServiceTaskViewSet(viewsets.ModelViewSet):
    queryset = ServiceTask.objects.all()
    serializer_class = serializers.ServiceTaskSerializer

class CalendarViewSet(viewsets.ModelViewSet):
    queryset = Calendar.objects.all()
    serializer_class = serializers.CalendarSerializer

# Events
class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = serializers.EventSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    def get_queryset(self):
        queryset = Event.objects.all()
        calendar_id = self.request.query_params.get('calendar_id', None)
        if calendar_id is not None:
            queryset = queryset.filter(calendar_id=calendar_id)
        return queryset

# ou cas ou je serialize moi meme ces events par dates (start, end) a partir de resa
def calendar_events(request):
    start = parse_datetime(request.GET.get('start'))
    end = parse_datetime(request.GET.get('end'))
    
    reservations = Reservation.objects.filter(check_in__gte=start, check_out__lte=end)
    
    events = []
    for reservation in reservations:
        events.append({
            'title': f"Réservation: {reservation.client}",
            'start': reservation.check_in.isoformat(),
            'end': reservation.check_out.isoformat(),
        })
    
    return JsonResponse(events, safe=False)

#----------------------------------------------------------
#--  Exemple d'API avec DRF pour afficher les tâches Celery 
#----------------------------------------------------------
class PeriodicTaskViewSet(viewsets.ModelViewSet):
    queryset = PeriodicTask.objects.all()
    serializer_class = PeriodicTaskSerializer

    def list(self, request):
        tasks = PeriodicTask.objects.all()
        serializer = PeriodicTaskSerializer(tasks, many=True)
        return Response(serializer.data)

#

class PeriodicTaskListCreate(generics.ListCreateAPIView):
    queryset = PeriodicTask.objects.all()
    serializer_class = PeriodicTaskSerializer
 


@api_view(['GET'])
def get_employee_tasks(request):
    """
    API pour obtenir le planning des tâches d'un ou plusieurs employés pour une semaine ou un mois donné.
    Paramètres de requête possibles :
    - employee_id : ID d'un employé spécifique (optionnel, si non fourni, on renvoie pour tous les employés)
    - year : Année concernée (obligatoire)
    - month : Mois concerné (optionnel, pour filtrer par mois)
    - week : Numéro de la semaine (optionnel, pour filtrer par semaine)
    """
    
    # Récupérer les paramètres de requête
    employee_id = request.query_params.get('employee_id', None)
    year = request.query_params.get('year', None)
    month = request.query_params.get('month', None)
    week = request.query_params.get('week', None)
    
    if not year:
        return Response({"error": "Le paramètre 'year' est obligatoire."}, status=400)
    
    # Filtrer les tâches par année
    tasks = ServiceTask.objects.filter(start_date__year=year)

    # Filtrer par mois si le paramètre est fourni
    if month:
        tasks = tasks.filter(start_date__month=month)

    # Filtrer par semaine si le paramètre est fourni
    if week:
        # Calculer les dates de début et de fin de la semaine
        first_day_of_year = datetime(int(year), 1, 1)
        start_of_week = first_day_of_year + timedelta(weeks=int(week) - 1, days=-first_day_of_year.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        
        tasks = tasks.filter(start_date__date__range=[start_of_week.date(), end_of_week.date()])

    # Filtrer par employé si un ID est fourni
    if employee_id:
        tasks = tasks.filter(employee__id=employee_id)

    # Sérialiser les tâches
    serializer = TaskSerializer(tasks, many=True)
    
    return Response(serializer.data)
