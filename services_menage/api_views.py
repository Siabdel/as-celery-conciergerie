import json
from decimal import Decimal
from decimal import Decimal, ROUND_HALF_UP
from django.shortcuts import render, HttpResponse
from django.urls import reverse
from django.contrib.auth.models import User
import requests
import pandas as pd
from datetime import datetime, timedelta, date
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
from services_menage import serializers as sm_serializers
from services_menage.serializers import PeriodicTaskSerializer
from rest_framework import status
from rest_framework.views import APIView
from core.models import CustomCalendar
from django.views.generic import CreateView

# Formulaire etat des lieu
from rest_framework import viewsets, status
from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.response import Response
##
from services_menage.serializers import CheckoutInventorySerializer
from services_menage.forms import CheckoutInventoryForm
#models
from services_menage import models as sm_models
from core import models as core_models
from dateutil.relativedelta import relativedelta
from dateutil import parser


class PeriodicTaskListCreate(generics.ListCreateAPIView):
    queryset = PeriodicTask.objects.all()
    serializer_class = PeriodicTaskSerializer

class PropertyViewSet(viewsets.ModelViewSet):
    queryset = sm_models.Property.objects.all()
    serializer_class = sm_serializers.PropertySerializer

class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = sm_models.Employee.objects.all()
    serializer_class = sm_serializers.EmployeeSerializer

class ReservationViewSet(viewsets.ModelViewSet):
    queryset = sm_models.Reservation.objects.all()
    serializer_class = sm_serializers.ReservationSerializer

class ServiceTaskViewSet(viewsets.ModelViewSet):
    queryset = sm_models.ServiceTask.objects.all()
    serializer_class = sm_serializers.ServiceTaskSerializer

class CalendarViewSet(viewsets.ModelViewSet):
    queryset = core_models.CustomCalendar.objects.all()
    serializer_class = sm_serializers.CalendarSerializer

# Events
class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = sm_serializers.EventSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    def get_queryset(self):
        queryset = Event.objects.all()
        calendar_id = self.request.query_params.get('calendar_id', None)
        if calendar_id is not None:
            queryset = queryset.filter(calendar_id=calendar_id)
        return queryset
## ---------------------------------------------------------
#--  AdditionalExpense ViewSet
#----------------------------------------------------------
class AdditionalExpenseViewSet(viewsets.ModelViewSet) : 
    queryset = sm_models.AdditionalExpense.objects.all()
    serializer_class = sm_serializers.AdditionalExpanseSerializer
    # permission_classes = [permissions.IsAuthenticated]
    # permission_classes = [permissions.AllowAny]  # ou [IsAuthenticated]
    

# additional endpoints if  needed
# Exemple pour filtrer par property
    def get_queryset(self):
        queryset = sm_models.AdditionalExpense.objects.all()
        property_id = self.request.query_params.get('property_id', None)
        if property_id is not None:
            queryset = queryset.filter(property_id=property_id)
        return queryset
    
# ---------------------------------------------------------
#--  AdditionalExpense ViewSet by Property
#----------------------------------------------------------
class PropertyAdditionalDepenseExpenseViewSet(viewsets.ModelViewSet) :
    queryset = sm_models.AdditionalExpense.objects.all()
    serializer_class = sm_serializers.AdditionalExpanseSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = sm_models.AdditionalExpense.objects.all()
        property_id = self.request.query_params.get('property_id', None)
        if property_id is not None:
            queryset = queryset.filter(property_id=property_id)
        return queryset
      

## ou cas ou je serialize moi meme ces events par dates (start, end) a partir de resa
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
    serializer = sm_serializers.ServiceTaskSerializer(tasks, many=True)
    
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


##-------------------------------
# Formulaire état des lieux
#------------------------------

class CheckoutInventoryViewSet(viewsets.ModelViewSet):
    queryset = sm_models.CheckoutInventory.objects.all()
    serializer_class = CheckoutInventorySerializer



@api_view(['PATCH'])
def update_event(request, pk):
    """
    Met à jour partiellement un événement via PATCH.
    """
    try:
        event = Event.objects.get(pk=pk)
    except Event.DoesNotExist:
        return Response({"error": "Event not found"}, status=status.HTTP_404_NOT_FOUND)
    
    # On récupère les nouvelles valeurs depuis la requête
    start_date_str = request.data.get('start_date')
    end_date_str = request.data.get('end_date')

    # Utiliser dateutil pour parser la date ISO 8601 avec fuseau horaire
    if start_date_str:
        start_date = parser.isoparse(start_date_str)  # Convertit automatiquement les dates ISO 8601
        event.start_date = start_date

    if end_date_str:
        end_date = parser.isoparse(end_date_str)
        event.end_date = end_date

    try:
        event.save()  # Enregistrer l'événement
    except ValueError as err:
        raise Exception("Erreur lors de l'enregistrement", err)

    # Sérialiser et renvoyer l'événement mis à jour
    serializer = serializers.EventSerializer(event)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
##def calculate_revenue_statement(property, start_date, end_date):
def calculate_revenue_statement(request ):
    """ 
    # Utilisation de la fonction
    property = Property.objects.get(id=1)  # Remplacer par l'ID de la propriété
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)

    statement = calculate_revenue_statement(property, start_date, end_date)
    print(f"Relevé des revenus du {statement['period_start']} au {statement['period_end']}:")
    print(f"Revenu total: {statement['total_revenue']}€")
    print(f"Dépenses totales: {statement['total_expenses']}€")
    print(f"Commission Airbnb: {statement['airbnb_commission']}€")
    print(f"Revenu net: {statement['net_revenue']}€")
    """

    # Calculer la période de 3 mois
    three_months_ago = datetime.now() - timedelta(days=90)

     # Récupérer les paramètres de requête
    property    = request.query_params.get('property', None)
    start_date  = request.query_params.get('start_date', None)
    end_date    = request.query_params.get('end_date', None)
    
    
    if start_date :
        start_date = max(start_date, three_months_ago)
    else :
        start_date = datetime.now()
        
    if not end_date:
        end_date = three_months_ago
        
    if not property :
        property = sm_models.Property.objects.get(pk=1)

    # Initialiser les variables
    total_revenue = Decimal('0.00')
    total_expenses = Decimal('0.00')
    airbnb_commission = Decimal('0.00')

    # Récupérer toutes les réservations pour cette période
    reservations = property.reservations.filter(check_in__gte=end_date, check_out__lte=start_date)

    releve_data = []
    releve_reservation = {
    }
    
    for reservation in reservations:
        # Calculer le revenu de la réservation
        reservation_revenue = reservation.total_price
        total_revenue += reservation_revenue

        # Calculer la commission Airbnb (supposons 3% du prix total)
        commission = reservation_revenue * Decimal('0.03')
        airbnb_commission += commission
        

    # Récupérer tous les frais pour cette période
    expenses = property.additional_expenses.filter(date__gte=start_date, date__lte=end_date)
    for expense in expenses:
        total_expenses += expense.amount

    # Ajouter la commission Airbnb aux dépenses totales
    total_expenses += airbnb_commission

    # Calculer le revenu net
    net_revenue = total_revenue - total_expenses

   
    # fonction qui transfomre 
    def round_decimal(value):
        return Decimal(value).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    
    reservations_dict = list(reservations.values())
    reservations_dict = [{k: int(v) if isinstance(v, Decimal) 
                            else v for k, v in item.items()} 
                                for item in reservations_dict]
    
    #raise Exception("resea =", list(reservations.values('id', 'check_in', 'check_out')))
    pp = sm_models.Property.objects.filter(pk=property.id)
    pro_dict =  list(elem for elem in pp.values())
    df = pd.DataFrame(pro_dict)
    owner = sm_models.User.objects.filter(pk=property.owner_id)
    pro_dict[0]['owner'] = owner.values('id', 'username', 'first_name', 'last_name')[0] 
    # Appliquer strftime aux champs de dates
    reservations_list = reservations.values(
        'created_at', 'check_in', 'check_out', 'guest_name', 'guest_email', 'platform',
        'number_of_guests', 'total_price', 'cleaning_fee', 'service_fee', 'guest_phone'
    )

    formatted_reservations_list = [
    {
        **reservation,
        'created_at': reservation['created_at'].strftime('%d/%m/%Y') if reservation['created_at'] else None,
        'check_in': reservation['check_in'].strftime('%d/%m/%Y') if reservation['check_in'] else None,
        'check_out': reservation['check_out'].strftime('%d/%m/%Y') if reservation['check_out'] else None,
    }
    for reservation in reservations_list
]
    
    # raise Exception("proprio =", pro_dict[0]['owner'])
    dataset = {
        'period_start': start_date.strftime("%d %B %Y"),
        'period_end': end_date,
        'total_revenue': round_decimal(total_revenue),
        'total_expenses': round_decimal(total_expenses),
        'airbnb_commission': round_decimal(airbnb_commission),
        'net_revenue': round_decimal(net_revenue),
        'property': pro_dict[0],
        'reservations': list(formatted_reservations_list),
    }
    ## 
    serializer = sm_serializers.DataRevenuePerPeriodeSerializer(data=dataset)
    if serializer.is_valid():
        return Response(serializer.data)
    else:
        print(serializer.errors)
        return Response(serializer.errors, status=400)

        
    
    

@api_view(['GET'])
def releve_activite_property(request):
    # cette url endpoint pour la liste des reservations par property
    # L'URL de base de votre API
    # base_url = "http://localhost:8000/pandas"
    # L'ID de la propriété dont vous voulez obtenir les réservations
    property_id = 10

    # Construire l'URL complète
    # url = f"{base_url}/properties/{property_id}/reservations/"
    # url = reverse('reservation-by-property', args=[10])  # Pour la propriété avec ID 10
    url = reverse('api-reservations-by-property', args=[10])  # Pour la propriété avec ID 10

    # Faire la requête GET
    response = requests.get(url)

    # Vérifier si la requête a réussi
    if response.status_code == 200:
        # La requête a réussi, vous pouvez accéder aux données
        reservations = response.json()
        print("Réservations pour la propriété 10:")
        for reservation in reservations:
            print(f"ID: {reservation['id']}, Date de début: {reservation['start_date']}, Date de fin: {reservation['end_date']}")
    else:
        # La requête a échoué
        print(f"Erreur lors de la récupération des réservations: {response.status_code}")
        print(response.text)



