
from datetime import datetime, timedelta
from django.utils.dateparse import parse_date
from django.utils.timezone import make_naive
from django.utils.dateparse import parse_datetime
from django.http import JsonResponse
from schedule.models import Event
# autre contrib 
from django_celery_beat.models import PeriodicTask
# DRF api rest
from rest_framework import viewsets, permissions, generics
from rest_framework.response import Response
from rest_framework.decorators import api_view
## 
from services_menage import models as sm_models
from core import models as core_models
from services_menage import serializers 
from services_menage.serializers import PeriodicTaskSerializer
from rest_framework import status
from rest_framework.views import APIView
from core.models import CustomCalendar

class PeriodicTaskListCreate(generics.ListCreateAPIView):
    queryset = PeriodicTask.objects.all()
    serializer_class = PeriodicTaskSerializer

class PropertyViewSet(viewsets.ModelViewSet):
    queryset = sm_models.Property.objects.all()
    serializer_class = serializers.PropertySerializer

class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = sm_models.Employee.objects.all()
    serializer_class = serializers.EmployeeSerializer

class ReservationViewSet(viewsets.ModelViewSet):
    queryset = sm_models.Reservation.objects.all()
    serializer_class = serializers.ReservationSerializer

class ServiceTaskViewSet(viewsets.ModelViewSet):
    queryset = sm_models.ServiceTask.objects.all()
    serializer_class = serializers.ServiceTaskSerializer

class CalendarViewSet(viewsets.ModelViewSet):
    queryset = core_models.CustomCalendar.objects.all()
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
    
    reservations = sm_models.Reservation.objects.filter(check_in__gte=start, check_out__lte=end)
    
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
    tasks = sm_models.ServiceTask.objects.filter(start_date__year=year)

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
    serializer = serializers.ServiceTaskSerializer(tasks, many=True)
    
    return Response(serializer.data)


@api_view(['POST'])
def get_employee_postask(request):
    """
    POST request for getting employee tasks for a given year and month.
    Expected payload:
    {
        "employee_id": 1,
        "year": 2024,
        "month": 10
    }
    """
    data = request.data
    
    # Récupérer l'identifiant de l'employé, l'année et le mois depuis le corps de la requête
    employee_id = data.get('employee_id')
    year = data.get('year')
    month = data.get('month')

    # Validation des paramètres reçus
    if not employee_id:
        return Response({"error": "Employee ID is required."}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        year = int(year)
        month = int(month)
        
        if month < 1 or month > 12:
            return Response({"error": "Invalid month value."}, status=status.HTTP_400_BAD_REQUEST)

    except (ValueError, TypeError):
        return Response({"error": "Year and month must be integers."}, status=status.HTTP_400_BAD_REQUEST)

    # Récupérer les tâches de l'employé pour l'année et le mois donnés
    tasks = ServiceTask.objects.filter(
        employee__id=employee_id,
        date__year=year,
        date__month=month
    )

    # Si aucune tâche n'est trouvée
    if not tasks.exists():
        return Response({"message": "No tasks found for the given employee and date."}, status=status.HTTP_404_NOT_FOUND)

    # Sérialiser et retourner la réponse
    serializer = TaskSerializer(tasks, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)



class ServiceTaskEventUpdateView(APIView):
    def patch(self, request, pk):
        """
        Met à jour partiellement un événement via PATCH.
        Seuls les champs `start_date` et `end_date` peuvent être modifiés.
        """
        try:
            event = sm_models.ServiceTask.objects.get(pk=pk)
            start_date_avant = event.start_date
        except sm_models.ServiceTask.DoesNotExist:
            return Response({"error": "Event not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # On récupère les nouvelles valeurs depuis la requête
        start_date_str = request.data.get('start_date')
        end_date_str = request.data.get('end_date')

        # Mettre à jour les champs si fournis
       
            
        # Convertir les chaînes de caractères en objets datetime
        # Définir le format de la chaîne de date (à ajuster selon le format des dates dans votre requête)
        date_format = "%Y-%m-%dT%H:%M:%S"  # Exemple : "2024-10-14T14:30:00"

        # Utiliser parse_datetime pour parser la date avec fuseau horaire
        if start_date_str:
            start_date = parse_datetime(start_date_str)  # Parse avec gestion du fuseau horaire
            event.start_date = start_date

        if end_date_str:
            end_date = parse_datetime(end_date_str)
            event.end_date = end_date
            
        # Sauvegarder les modifications
        try :
            event.save()
            #raise Exception( f"erreur de save  {start_date_avant} apres {event.start_date } ")
        except Exception as err :
            raise Exception("erreur de save ", err)

        # Sérialiser et renvoyer l'événement mis à jour
        serializer = serializers.ServiceTaskSerializer(event)
        return Response(serializer.data, status=status.HTTP_200_OK)
