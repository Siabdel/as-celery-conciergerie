
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
    fullname = serializers.SerializerMethodField()
    photo = serializers.SerializerMethodField()

    class Meta:
        model = Employee
        fields = ['id', 'user', 'role', 'is_active', 'phone_number', 'photo', 'fullname']
    
    def get_fullname(self, obj):
        if obj.user:
            return f"{obj.user.first_name} {obj.user.last_name}".strip()
        return ""

    def get_photo(self, obj):
        # si vous avez un champ image ; sinon avatar externe
        if obj.user:
            return f"https://ui-avatars.com/api/?name={obj.user.first_name}+{obj.user.last_name}&background=6366f1&color=fff"
        return "https://ui-avatars.com/api/?name=Unknown&background=6366f1&color=fff"

# Service Serializer
class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = '__all__'

class AbsenceSerializer(serializers.ModelSerializer):
    employee = EmployeeSerializer(read_only=True)

    class Meta:
        model = Absence
        fields = ['id', 'employee', 'start_date', 'end_date', 'type_absence', 'description']

# -------------------- TASKS --------------------
class ServiceTaskShortSerializer(serializers.ModelSerializer):
    property_name = serializers.CharField(source='property.name', read_only=True)
    employee_name = serializers.SerializerMethodField()

    class Meta:
        model = ServiceTask
        fields = ['id', 'property_name', 'employee_name', 'start_date', 'end_date', 'type_service', 'completed']
    
    def get_employee_name(self, obj):
        if obj.employee and obj.employee.user:
            return obj.employee.user.get_full_name()
        return ""
