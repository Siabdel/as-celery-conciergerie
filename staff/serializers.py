
# conciergerie/serializers.py
from rest_framework import serializers
from staff.models import Employee, Absence, Service
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from conciergerie.models import ServiceTask


User = get_user_model()

class UserSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'username', 'email']

# Employee Serializer
class EmployeeSerializer(serializers.ModelSerializer):
    user = UserSimpleSerializer(read_only=True)
    full_name = serializers.SerializerMethodField()
    class Meta:
        model = Employee
        fields = '__all__'
    
    def get_full_name(self, obj):
        if obj.user:
            return f"{obj.user.first_name} {obj.user.last_name}".strip()
        return ""

# Absence Serializer
class AbsenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Absence
        fields = '__all__'

# Service Serializer
class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = '__all__'



# -------------------- STAFF --------------------
class UserShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'username']

class EmployeeSerializer(serializers.ModelSerializer):
    user = UserShortSerializer(read_only=True)
    photo = serializers.SerializerMethodField()

    class Meta:
        model = Employee
        fields = ['id', 'user', 'role', 'is_active', 'phone_number', 'photo']

    def get_photo(self, obj):
        # si vous avez un champ image ; sinon avatar externe
        return f"https://ui-avatars.com/api/?name={obj.user.first_name}+{obj.user.last_name}&background=6366f1&color=fff"

class AbsenceSerializer(serializers.ModelSerializer):
    employee = EmployeeSerializer(read_only=True)

    class Meta:
        model = Absence
        fields = ['id', 'employee', 'start_date', 'end_date', 'type_absence', 'description']

# -------------------- TASKS --------------------
class ServiceTaskShortSerializer(serializers.ModelSerializer):
    property_name = serializers.CharField(source='property.name', read_only=True)
    employee_name = serializers.CharField(source='employee.user.get_full_name', read_only=True)

    class Meta:
        model = ServiceTask
        fields = ['id', 'property_name', 'employee_name', 'start_date', 'end_date', 'type_service', 'completed']