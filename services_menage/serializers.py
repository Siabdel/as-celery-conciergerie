
from rest_framework import serializers
from .models import Employee, Reservation, CleaningTask
from schedule.models import Calendar, Event

class CalendarSerializer(serializers.ModelSerializer):
    class Meta:
        model = Calendar
        fields = ['id', 'name', 'slug']

class EmployeeSerializer(serializers.ModelSerializer):
    calendar = CalendarSerializer(read_only=True)

    class Meta:
        model = Employee
        fields = ['id', 'name', 'calendar']

class ReservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reservation
        fields = ['id', 'client', 'check_in', 'check_out']

class CleaningTaskSerializer(serializers.ModelSerializer):
    reservation = ReservationSerializer(read_only=True)
    employee = EmployeeSerializer(read_only=True)

    class Meta:
        model = CleaningTask
        fields = ['id', 'reservation', 'employee', 'scheduled_time']

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