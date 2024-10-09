
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from django.db.models.signals import post_save
from django.dispatch import receiver
from services_menage import views
from services_menage import models as serv_models
        
# 5. Utilisez des signaux pour automatiser la création d'événements :

@receiver(post_save, sender=serv_models.Reservation)
def reservation_created(sender, instance, created, **kwargs):
    if created:
        # Obtenir la date actuelle
        date_actuelle = datetime.now()
        # Obtenir le dernier jour de l'année en cours
        fin_annee = datetime(date_actuelle.year, 12, 31)
        # Initialiser la date du mois en cours
        date_mois = date_actuelle.replace(day=1)

        # Boucle pour afficher les mois restants de l'année
        while date_mois <= fin_annee:
            ## print(date_mois.strftime("%B %Y"))
            views.assign_tasks_from_reservations_with_balancing(date_mois.year, date_mois.month)
            # Passer au mois suivant
            if date_mois.month == 12:
                break
            date_mois = (date_mois + timedelta(days=32)).replace(day=1)
                

"""
@receiver(post_save, sender=serv_models.Reservation)
def creer_tache_nettoyage(sender, instance, created, **kwargs):
	planifier_nettoyage(sender, instance, created)
""" 