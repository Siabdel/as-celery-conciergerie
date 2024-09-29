
from rest_framework import viewsets
from .models import Employee, Reservation, MaintenanceTask
from schedule.models import Calendar, Event
from rest_framework import viewsets, permissions
from services_menage import serializers 
from django.utils.dateparse import parse_datetime
from django.http import JsonResponse
from rest_framework import generics
from django_celery_beat.models import PeriodicTask
from .serializers import PeriodicTaskSerializer

class PeriodicTaskListCreate(generics.ListCreateAPIView):
    queryset = PeriodicTask.objects.all()
    serializer_class = PeriodicTaskSerializer



class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.all()
    serializer_class = serializers.EmployeeSerializer

class ReservationViewSet(viewsets.ModelViewSet):
    queryset = Reservation.objects.all()
    serializer_class = serializers.ReservationSerializer

class MaintenanceTaskViewSet(viewsets.ModelViewSet):
    queryset = MaintenanceTask.objects.all()
    serializer_class = serializers.MaintenanceTaskSerializer

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
 