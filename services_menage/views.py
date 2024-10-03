import json
from django.shortcuts import render, HttpResponse
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from schedule.models.calendars import Calendar
from services_menage import models as serv_models
from schedule.models import Event
from services_menage.models import  Calendar
from django.utils.timezone import now
from django_celery_beat.models import PeriodicTask, IntervalSchedule


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
        checkin_checkout()
        

def create_reservation_event(reservation):
    main_calendar = Calendar.objects.get(name="Reservations")
    Event.objects.create(
        start=reservation.check_in,
        end=reservation.check_out,
        title=f"Guest: {reservation.guest_name}, Réservation: {reservation.property}",

        calendar=main_calendar
    )

"""
@receiver(post_save, sender=serv_models.Reservation)
def creer_tache_nettoyage(sender, instance, created, **kwargs):
	planifier_nettoyage(sender, instance, created)
""" 

## Planiffier service Menage
def planifier_nettoyage(sender, instance, created, **kwargs):
    if created:
        # Calcul du délai en secondes jusqu'à la date de check-out
        intervalle = (instance.check_out - now()).total_seconds()
        # Créer une tâche périodique à exécuter après la check-out
        schedule, created = IntervalSchedule.objects.get_or_create(every=int(intervalle), 
                                                        period=IntervalSchedule.SECONDS)
        PeriodicTask.objects.create(
            interval=schedule,
            name=f"Nettoyage pour {instance.property} à {instance.check_out}",
            task='services_menage.task',
            args=json.dumps([instance.id])
        )
   
   
   
def checkin_checkout():
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
        