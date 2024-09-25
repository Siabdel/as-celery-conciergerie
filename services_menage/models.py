from django.db import models
from schedule.models import Event, Calendar

class Reservation(models.Model):
    client = models.CharField(max_length=100)
    check_in = models.DateTimeField()
    check_out = models.DateTimeField()

class Employee(models.Model):
    name = models.CharField(max_length=100)
    calendar = models.ForeignKey(Calendar, on_delete=models.CASCADE)

class CleaningTask(models.Model):
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE)
    employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True)
    scheduled_time = models.DateTimeField()