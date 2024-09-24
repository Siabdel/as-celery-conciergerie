from django.shortcuts import render
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from schedule.models.calendars import Calendar
from services_menage import models as ser_models


## Logique

## 1. Créez un calendrier principal pour les réservations :

main_calendar = Calendar.objects.get_or_create(name="Reservations", slug="Reservations")

# 2. Créez un calendrier pour chaque employé :

for employee in ser_models.Employee.objects.all():
    employee.calendar = Calendar.objects.create(name=f"Calendrier de {employee.name}")
    employee.save()

# 3. Lorsqu'une réservation est créée, ajoutez-la au calendrier principal :

def create_reservation_event(reservation):
    Event.objects.create(
        start=reservation.check_in,
        end=reservation.check_out,
        title=f"Réservation: {reservation.client}",
        calendar=main_calendar
    )

# 4. Planifiez une tâche de nettoyage après chaque départ :


def schedule_cleaning(reservation):
    cleaning_time = reservation.check_out + timezone.timedelta(hours=2)
    available_employee = find_available_employee(cleaning_time)
    
    if available_employee:
        cleaning_task = CleaningTask.objects.create(
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

def find_available_employee(cleaning_time):
    for employee in Employee.objects.all():
        if not Event.objects.filter(
            calendar=employee.calendar,
            start__lte=cleaning_time,
            end__gte=cleaning_time
        ).exists():
            return employee
    return None

# 5. Utilisez des signaux pour automatiser la création d'événements :


@receiver(post_save, sender=ser_models.Reservation)
def reservation_created(sender, instance, created, **kwargs):
    if created:
        create_reservation_event(instance)
        schedule_cleaning(instance)


## Créez des vues pour afficher les calendriers :
def main_calendar_view(request):
    return render(request, 'main_calendar.html', {
        'calendar': main_calendar
    })

def employee_calendar_view(request, employee_id):
    employee = Employee.objects.get(id=employee_id)
    return render(request, 'employee_calendar.html', {
        'calendar': employee.calendar,
        'employee': employee
    })

## Templates
