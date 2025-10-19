
from rest_framework import serializers
from schedule.models import Calendar, Event
from django_celery_beat.models import PeriodicTask
import services_menage.models as sm_models
from django.contrib.auth.models import User, Group, Permission

class UserSerializer(serializers.ModelSerializer):
    class Meta :
        model = User
        fields = '__all__'
        #fields = ['id', 'username', 'email']  # Champs à exposer

class CustomPeriodicTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = PeriodicTask
        fields = '__all__'


class CalendarSerializer(serializers.ModelSerializer):
    class Meta:
        model = Calendar
        fields = ['id', 'name', 'slug']

class PropertySerializer(serializers.ModelSerializer):
    owner = UserSerializer()
    class Meta:
        model = sm_models.Property
        fields__ = '__all__'
        fields = ( "id", "created_at", "name", "type", "address",
            "price_per_night",  "owner",
        )

    def get_client(self, obj):
        return obj.owner.user.first_name


class EmployeeSerializer(serializers.ModelSerializer):
    calendar = CalendarSerializer(read_only=True)

    class Meta:
        model = sm_models.Employee
        fields = ['id', 'name', 'user', 'phone_number', 'calendar']

class EventSerializer(serializers.ModelSerializer):
    
    calendar = CalendarSerializer(read_only=True)
    calendar_id = serializers.PrimaryKeyRelatedField(
        queryset=Calendar.objects.all(),
        source='calendar',
        write_only=True
    )

    class Meta:
        model = Event
        fields = ['id', 'start', 'end', 'title', 'description', 'created_on', 'updated_on', 
                  'calendar', 'calendar_id', 'creator', 'rule', 'end_recurring_period', 'color_event']
        read_only_fields = ['created_on', 'updated_on']

    def validate(self, data):
        if data['end'] < data['start']:
            raise serializers.ValidationError("End time must be later than start time.")
        return data
    
class PeriodicTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = PeriodicTask
        fields = '__all__'

 
# construire une API pour ceer des events pour Calendar
class ReservationSerializer(serializers.ModelSerializer):
    ##id = serializers.CharField(source='pk')
    title = serializers.SerializerMethodField()
    #start = serializers.DateTimeField(source='check_in')
    #end = serializers.DateTimeField(source='check_out')

    start = serializers.SerializerMethodField()  
    end = serializers.SerializerMethodField()
    ## bgColor = serializers.CharField(default='#00a9ff')
    ## color = serializers.CharField(default='white')
    
    def get_start(self, obj):
        return obj.check_in.isoformat()

    def get_end(self, obj):
        return obj.check_out.isoformat()

    def get_title(self, obj):
        return f"Reservation for {obj.property.name}"

    def update(self, instance, validated_data):
        instance.check_in = validated_data.get('check_in', instance.check_in)
        instance.check_out = validated_data.get('check_out', instance.check_out)
        instance.guest_name = validated_data.get('guest_name', instance.guest_name)
        # Mettez à jour d'autres champs si nécessaire
        instance.save()
        return instance
    
    def validate(self, data):
        if data['check_in'] >= data['check_out']:
            raise serializers.ValidationError("End date must be after start date")
        return data

 
    class Meta:
        model = sm_models.Reservation
        fields = '__all__'
        fields__ = [ 'id', 'title', 'start', 'end', 'guest_name', 'guest_email', 
                  'check_in', 'check_out', 'property',  
                  'reservation_status', 'number_of_guests', 'total_price',
                  ]
        extra_kwargs = {
            'property': {'required': False}  # Rend le champ 'property' optionnel pour les mises à jour
        }

        
class ServiceTaskSerializer(serializers.ModelSerializer):
    reservation = ReservationSerializer(read_only=True)
    employee = EmployeeSerializer(read_only=True)
    start = serializers.SerializerMethodField()  
    end = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()
   
    def get_start(self, obj):
        return obj.start_date.isoformat()

    def get_end(self, obj):
        return obj.end_date.isoformat()

    def get_title(self, obj):
        if obj.type_service and obj.property and obj.employee:
            if obj.type_service == TaskTypeService.CHECKED_IN :    
                return f"Check-in for {obj.property.name} by {obj.employee.name}"
            elif obj.type_service == TaskTypeService.CHECKED_OUT :
                return f"Check-out for {obj.property.name} by {obj.employee.name}"
            elif obj.type_service == TaskTypeService.CLEANING : 
                return f"Cleaning for {obj.property.name} by {obj.employee.name}"
            elif obj.type_service == TaskTypeService.ERROR:
                return f"Erreur Impossible d'assigner un employé pour le {obj.type_service} à {obj.start_date}",
            else:
                return obj.description[:20]

    class Meta:
        model = sm_models.ServiceTask
        fields = ['id', 'title', 'type_service', 'employee', 'reservation', 'employee', 'property', 'start', 'end', ]


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = sm_models.ServiceTask
        fields = ['id', 'description', 'start_date', 'end_date', 'employee', 'reservation']
        depth = 1  # Optionnel, si vous souhaitez inclure les détails des relations (employee, reservation)



class DataReservationsSerializer(serializers.Serializer):
    # Champs formatés
    #formatted_check_in = serializers.SerializerMethodField()
    #formatted_check_out = serializers.SerializerMethodField()

    created_at  = serializers.CharField()
    check_in    = serializers.CharField()
    check_out   = serializers.CharField()
    guest_name  = serializers.CharField()
    guest_email = serializers.CharField()
    platform    = serializers.CharField()
    # les tottaux 
    number_of_guests = serializers.IntegerField()
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    cleaning_fee = serializers.DecimalField(max_digits=10, decimal_places=2)
    service_fee = serializers.DecimalField(max_digits=10, decimal_places=2)
    guest_phone = serializers.CharField()
    
    def get_formatted_check_in(self, obj):
        return obj.check_in.strftime('%d/%m/%Y') if obj.check_in else None

    def get_formatted_check_out(self, obj):
        return obj.check_out.strftime('%d/%m/%Y') if obj.check_out else None
   

class PropertyPrimarySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    address = serializers.CharField()
    price_per_night = serializers.DecimalField(max_digits=10, decimal_places=2)
    owner = serializers.JSONField()  # JSON pour inclure les informations du propriétaire

class DataRevenuePerPeriodeSerializer(serializers.Serializer):
    property = PropertyPrimarySerializer()
    
    # les totaux 
    period_start = serializers.CharField()
    period_end = serializers.DateTimeField()
    total_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_expenses = serializers.DecimalField(max_digits=10, decimal_places=2)
    airbnb_commission = serializers.DecimalField(max_digits=10, decimal_places=2)
    net_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    # reservations 
    reservations = DataReservationsSerializer(many=True)


class AdditionalExpanseSerializer(serializers.ModelSerializer):
    class Meta:
        model = sm_models.AdditionalExpense
        fields = '__all__'
        #fields = ['id', 'property', 'expense_type', 'amount', 'date', 'description', 'notes', 'is_recurring', 'recurrence_interval', 'created_at', 'updated_at', 'created_by', 'updated_by', 'date_incurred']
        
        description = serializers.CharField()
        amount = serializers.DecimalField(max_digits=10, decimal_places=2)
        property = PropertyPrimarySerializer()  
        notes = serializers.CharField()  # Notes supplémentaires
        is_recurring = serializers.BooleanField()  # Indique si la dépense est récurrente
        recurrence_interval = serializers.CharField()  # Intervalle de récurrence (mensuel, annuel, etc.)
        created_at = serializers.DateTimeField()  # Date de création de la dépense
        updated_at = serializers.DateTimeField()  # Date de la dernière mise à jour de la dépense
        created_by = UserSerializer()  # Utilisateur qui a créé la dépense
        updated_by = UserSerializer()  # Utilisateur qui a mis à jour la dépense
        date_incurred = serializers.DateField()  # Date à laquelle la dépense a
        
        created_by = UserSerializer()  # Utilisateur associé à la dépense
        updated_by = UserSerializer()  # Utilisateur ayant modifié la dépense
    
    def validate_amount(self, value):
        if value < 0:
            raise serializers.ValidationError("Amount must be a positive value.")
        return value
    def validate_date_incurred(self, value):
        from datetime import date
        if value > date.today():
            raise serializers.ValidationError("Date incurred cannot be in the future.")
        return value
    def validate_next_occurrence(self, value):
        from datetime import date
        if self.initial_data.get('is_recurring') and value <= date.today():
            raise serializers.ValidationError("Next occurrence must be a future date for recurring expenses.")
        return value
    def validate(self, data):
        if data.get('is_recurring') and not data.get('recurrence_interval'):
            raise serializers.ValidationError("Recurrence interval is required for recurring expenses.")
        return data
class ReservationStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = sm_models.ReservationStatus
        fields = '__all__'
#-------------------
# CheckinInventory Serializer
#-------------------------------
from .models import CheckoutInventory

class CheckoutInventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = CheckoutInventory
        model  = sm_models.CheckoutInventory
        
        fields = '__all__'