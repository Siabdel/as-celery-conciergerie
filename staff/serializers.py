
from rest_framework import serializers
from staff.models import Employee, Absence, Service
from django.contrib.auth import get_user_model

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

