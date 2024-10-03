
from datetime import datetime
from celery import shared_task
from .models import Reservation, MaintenanceTask
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from schedule.models.calendars import Calendar
from schedule.models import Event, Calendar
from services_menage import models as serv_models


@shared_task
# 1. faire un etat de lieu après chaque départ :
def faire_etat_des_lieu_appart(reservation_id):
    # Logique pour nettoyer la chambre
    print(f" faire_etat_des_lieu_appart apres check_out {reservation_id}")
    # Ajoutez ici la logique réelle de nettoyage

# 2. Planifiez une tâche de nettoyage après chaque départ :
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
        
# 4. Planifiez de tache de check_in a l'Entrée du client, check_out après chaque départ :
@shared_task
def checkin_checkout_task():
    #raise Exception("schedule_checkin_checkout ")
    ##futur_resevations = Reservation.objects.filter(start__gte=timezone.now())
    
    futur_resevations = serv_models.Reservation.objects.all()
    ## 1. Créez un calendrier principal pour les réservations :
    main_calendar = Calendar.objects.get(slug="reservations")

    for reservation in futur_resevations:
        ## get calendar 
        ## create Event check-in
        event_in = Event.objects.get_or_create(
            calendar = main_calendar,
            start = reservation.check_in,
            end = reservation.check_in + timezone.timedelta(hours=1),
            title=f"Check_in guest_name = {reservation.guest_name}, Chambre de {reservation.property}"
        )
        
        ## create Event check-out
        Event.objects.get_or_create(
            calendar = main_calendar,
            start = reservation.check_out,
            end = reservation.check_out + timezone.timedelta(hours=1),
            title=f"Check_out guest_name = {reservation.guest_name}, Chambre de {reservation.property}"
        )
        
# 4. touvez des employees diponible
def find_available_employee(cleaning_time):
    for employee in serv_models.Employee.objects.all():
        if not Event.objects.filter(
            calendar=employee.calendar,
            start__lte=cleaning_time,
            end__gte=cleaning_time
        ).exists():
            return employee
    return None