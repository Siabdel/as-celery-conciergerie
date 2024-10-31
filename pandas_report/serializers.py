from rest_framework import serializers
from schedule.models import Calendar, Event
from django_celery_beat.models import PeriodicTask
from services_menage.models import Employee, Reservation, ServiceTask, Property
from services_menage.models import ResaStatus, TaskTypeService


class RevenuesSerializer(serializers.DictField):
    child = serializers.FloatField()

class DatasetSerializer(serializers.Serializer):
    property_name = serializers.CharField()
    revenues = RevenuesSerializer()
    total = serializers.FloatField()

class RevenueReportSerializer(serializers.Serializer):
    dataset = DatasetSerializer()

class RevenueReportListSerializer(serializers.ListSerializer):
    child = RevenueReportSerializer()