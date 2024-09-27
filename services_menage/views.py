from django.shortcuts import render, HttpResponse
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from schedule.models.calendars import Calendar
from services_menage import models as ser_models
from schedule.models import Event, Calendar



## Calendar
def calendar_home(request):
    return render(request, 'fullcalendar_v5.html')

## Logique
def init_create(requete):

    ## 1. Créez un calendrier principal pour les réservations :
    main_calendar = Calendar.objects.get_or_create(name="Reservations", slug="Reservations")

    # 2. Créez un calendrier pour chaque employé :
    for employee in ser_models.Employee.objects.all():
        employee.calendar = Calendar.objects.create(name=f"Calendrier de {employee.name}")
        employee.save()

    # 3. Lorsqu'une réservation est créée, ajoutez-la au calendrier principal :
    return HttpResponse("Init Calendar ...")


# 4. Planifiez une tâche de nettoyage après chaque départ :
# 5. Utilisez des signaux pour automatiser la création d'événements :

@receiver(post_save, sender=ser_models.Reservation)
def reservation_created(sender, instance, created, **kwargs):
    if created:
        create_reservation_event(instance)
        schedule_cleaning(instance)

def create_reservation_event(reservation):
    main_calendar = Calendar.objects.get(name="Reservations")
    Event.objects.create(
        start=reservation.start_date,
        end=reservation.end_date,
        title=f"Réservation: {reservation.property}",
        calendar=main_calendar
    )

# 4. Planifiez une tâche de nettoyage après chaque départ :
def schedule_cleaning(reservation):
    cleaning_time = reservation.end_date + timezone.timedelta(hours=2)
    available_employee = find_available_employee(cleaning_time)
    
    if available_employee:
        cleaning_task = ser_models.MaintenanceTask.objects.create(
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