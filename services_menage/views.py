from django.shortcuts import render, HttpResponse
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from schedule.models.calendars import Calendar
from services_menage import models as serv_models
from schedule.models import Event, Calendar
from .admin import planifier_nettoyage



## Calendar
def calendar_home(request):
    return render(request, 'fullcalendar_v5.html')

## Logique
def init_create(requete):

    ## 1. Créez un calendrier principal pour les réservations :
    main_calendar = Calendar.objects.get_or_create(name="Reservations", slug="Reservations")

    # 2. Créez un calendrier pour chaque employé :
    for employee in serv_models.Employee.objects.all():
        employee.calendar = Calendar.objects.create(name=f"Calendrier de {employee.name}")
        employee.save()

    # 3. Lorsqu'une réservation est créée, ajoutez-la au calendrier principal :
    return HttpResponse("Init Calendar ...")


# 4. Planifiez une tâche de nettoyage après chaque départ :
# 5. Utilisez des signaux pour automatiser la création d'événements :

@receiver(post_save, sender=serv_models.Reservation)
def reservation_created(sender, instance, created, **kwargs):
    if created:
        create_reservation_event(instance)
        planifier_nettoyage(sender, instance, created)
        # schedule_cleaning(instance)

def create_reservation_event(reservation):
    main_calendar = Calendar.objects.get(name="Reservations")
    Event.objects.create(
        start=reservation.start_date,
        end=reservation.end_date,
        title=f"Réservation: {reservation.property}",
        calendar=main_calendar
    )

"""
@receiver(post_save, sender=serv_models.Reservation)
def creer_tache_nettoyage(sender, instance, created, **kwargs):
	planifier_nettoyage(sender, instance, created)
""" 