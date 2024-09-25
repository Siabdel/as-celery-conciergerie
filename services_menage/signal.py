
from django.db.models.signals import post_save
from django.dispatch import receiver
from services_menage import views

@receiver(post_save, sender=Reservation)
def reservation_created(sender, instance, created, **kwargs):
    if created:
        views.create_reservation_event(instance)
        views.schedule_cleaning(instance)
        ## views.schedule_cleaning.delay(instance.id)