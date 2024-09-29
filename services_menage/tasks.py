
from celery import shared_task
from .models import Reservation, MaintenanceTask
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from schedule.models.calendars import Calendar
from schedule.models import Event, Calendar


@shared_task
def faire_etat_des_lieu_appart(reservation_id):
    # Logique pour nettoyer la chambre
    print(f" faire_etat_des_lieu_appart apres check_out {reservation_id}")
    # Ajoutez ici la logique réelle de nettoyage

@shared_task
def service_menage_task(reservation_id):
    reservation = Reservation.objects.get(id=reservation_id)
    cleaning_time = reservation.check_out + timezone.timedelta(hours=2)
    available_employee = find_available_employee(cleaning_time)
    
    if available_employee:
        cleaning_task = MaintenanceTask.objects.create(
            reservation=reservation,
            employee=available_employee,
            scheduled_time=cleaning_time
        )
        
        Event.objects.create(
            start=cleaning_time,
            end=cleaning_time + timezone.timedelta(hours=2),
            title=f"Nettoyage: Chambre de {reservation.client}",
            calendar=available_employee.calendar
        )
        
        # 4. Planifiez une tâche de nettoyage après chaque départ :
def schedule_cleaning(reservation):
    cleaning_time = reservation.end_date + timezone.timedelta(hours=2)
    available_employee = find_available_employee(cleaning_time)
    
    if available_employee:
        cleaning_task = MaintenanceTask.objects.create(
            property=reservation.property,
            employee=available_employee,
            due_date=cleaning_time
        )
        
        Event.objects.create(
            start=cleaning_time,
            end=cleaning_time + timezone.timedelta(hours=2),
            title=f"Nettoyage: Chambre de {reservation.property}",
            calendar=available_employee.calendar
        )
 
# 4. touvez des employees diponible
def find_available_employee(cleaning_time):
    for employee in ser_models.Employee.objects.all():
        if not Event.objects.filter(
            calendar=employee.calendar,
            start__lte=cleaning_time,
            end__gte=cleaning_time
        ).exists():
            return employee
    return None