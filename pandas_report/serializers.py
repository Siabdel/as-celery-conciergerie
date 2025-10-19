from rest_framework import serializers
from schedule.models import Calendar, Event
from django_celery_beat.models import PeriodicTask
from services_menage.models import Employee, Reservation, ServiceTask, Property
from services_menage.models import ReservationStatus, TaskTypeService


#--------------------------------------------------------
#-- Rapport Analytique des revenues par mois / property
#--------------------------------------------------------


class RevenueSerializer(serializers.Serializer):
    month = serializers.CharField()
    revenue = serializers.FloatField()


class DatasetItemSerializer(serializers.Serializer):
    property_name = serializers.CharField()
    revenues = RevenueSerializer()
    total = serializers.FloatField()

class RevenueReportSerializer(serializers.Serializer):
    dataset = DatasetItemSerializer(many=True)

#--------------------------------------------------------
#-- 
"""_summary_ * Taux d'occupation par propriété Montre le pourcentage de jours réservés par 
mois pour chaque propriété Aide à identifier les périodes creuses et les opportunités d'optimisation

* 
nombre de jours réservés par mois pour chaque propriété avec la bibliothèque Pandas, nous devons :

Récupérer les données depuis Django ORM.
Convertir les données en un DataFrame Pandas.
Calculer les jours réservés pour chaque réservation.
Grouper les données par mois et propriété pour obtenir la somme des jours réservés.
"""
#--------------------------------------------------------

class DatasetOccupationSerializer(serializers.Serializer):
    month = serializers.CharField()
    property_name = serializers.CharField()
    total_days_reserved = serializers.IntegerField()

class TauxOccupationSerializer(serializers.Serializer):
    # Champ pour la liste des données
    datatest = DatasetOccupationSerializer(many=True)

##-----------------------------------
##-- class 
##-----------------------------------
#--------------------------------------------------------
#-- Rapport Analytique des revenues par mois / property
#-------------------------------------------------------
class DataPropretySerializer(serializers.Serializer):
    month = serializers.CharField()
    revenue = serializers.FloatField()

class RevenuePropriotytSerializer(serializers.Serializer):
    dataset = DataPropretySerializer(many=True)
    

class OccupancyRateSerializer(serializers.Serializer):
    month = serializers.CharField()
    occupancy_rate = serializers.FloatField()

class OccupancyDataSerializer(serializers.Serializer):
    dataset = OccupancyRateSerializer(many=True)

class DataPriceEvolutionSerializer(serializers.Serializer):
    month = serializers.CharField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    season = serializers.CharField()

class PriceEvolutionSerializer(serializers.Serializer):
    dataset = DataPriceEvolutionSerializer(many=True)