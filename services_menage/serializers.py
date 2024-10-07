
from rest_framework import serializers
from .models import Employee, Reservation, ServiceTask
from schedule.models import Calendar, Event
from django_celery_beat.models import PeriodicTask
class CustomPeriodicTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = PeriodicTask
        fields = '__all__'


class CalendarSerializer(serializers.ModelSerializer):
    class Meta:
        model = Calendar
        fields = ['id', 'name', 'slug']

class EmployeeSerializer(serializers.ModelSerializer):
    calendar = CalendarSerializer(read_only=True)

    class Meta:
        model = Employee
        fields = ['id', 'name', 'calendar']

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
        model = Reservation
        fields = [ 'id', 'title', 'start', 'end', 'guest_name', 'guest_email', 
                  'check_in', 'check_out', 'property',  
                  'reservation_status', 'number_of_guests', 'total_price',
                  ]
        extra_kwargs = {
            'property': {'required': False}  # Rend le champ 'property' optionnel pour les mises à jour
        }

        
class ServiceTaskSerializer(serializers.ModelSerializer):
    reservation = ReservationSerializer(read_only=True)
    employee = EmployeeSerializer(read_only=True)

    class Meta:
        model = ServiceTask
        fields = ['id', 'reservation', 'employee', 'scheduled_time']
