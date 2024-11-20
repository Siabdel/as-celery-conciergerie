
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import F
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from services_menage import views
from .models import Reservation, ResaStatus
from services_menage import models as serv_models

        
# 5. Utilisez des signaux pour automatiser la création d'événements :

@receiver(post_save, sender=serv_models.Reservation)
def reservation_created(sender, instance, created, **kwargs):
    if not created:
        # Obtenir la date actuelle
        date_actuelle = timezone.now().date()
        # Obtenir le dernier jour de l'année en cours
        fin_annee = datetime(date_actuelle.year, 12, 31).date()
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


@receiver(pre_save, sender=Reservation)
def update_reservation_status(sender, instance, **kwargs):
    aujourdhui = timezone.now()

    # Si la réservation est annulée, c'est prioritaire sur tous les autres statuts
    if hasattr(instance, 'cancelled_at') and instance.cancelled_at is not None:
        instance.reservation_status = ResaStatus.CANCELLED
        return  # On arrête ici pour ne pas continuer à changer le statut

    # Grace period (période de grâce) pour certains statuts
    grace_period = timezone.timedelta(hours=2)

    # Si la réservation est "PENDING" (en attente)
    if instance.reservation_status == ResaStatus.PENDING:
        if aujourdhui >= (instance.check_in + grace_period):
            instance.reservation_status = ResaStatus.NEEDS_ATTENTION
            # Envoyer une notification à l'équipe de gestion
            #send_notification_to_management(instance)
        elif aujourdhui >= (instance.check_in + timezone.timedelta(hours=24)):
            instance.reservation_status = ResaStatus.EXPIRED

    # Si la réservation est "CONFIRMED" (confirmée)
    elif instance.reservation_status == ResaStatus.CONFIRMED:
        if instance.check_in <= aujourdhui < instance.check_out:
            instance.reservation_status = ResaStatus.CHECKED_IN

    # Si la réservation est "CHECKED_IN" (en cours)
    elif instance.reservation_status == ResaStatus.CHECKED_IN or \
            instance.reservation_status == ResaStatus.IN_PROGRESS :
        if aujourdhui >= instance.check_out:
            instance.reservation_status = ResaStatus.CHECKED_OUT

    # Si la réservation est "CHECKED_OUT" (terminée)
    elif instance.reservation_status == ResaStatus.CHECKED_OUT:
        if aujourdhui >= (instance.check_out + timezone.timedelta(hours=24)):
            instance.reservation_status = ResaStatus.COMPLETED

    # Si la réservation est "IN_PROGRESS" et que la date de check-out est dépassée
    elif instance.reservation_status == ResaStatus.IN_PROGRESS and instance.check_out < aujourdhui:
        instance.reservation_status = ResaStatus.EXPIRED
    elif not instance.reservation_status :
        instance.reservation_status = ResaStatus.PENDING
        
        

    # Si le statut est "EXPIRED", on ne le change pas
    # L'expiration n'est pas réversible à ce stade.

    # Pour mettre à jour l'heure de check-in à 14h00 et l'heure de check-out à 11h00 pour toutes les réservations
    """
    Reservation.objects.update(
        check_in=F('check_in').replace(hour=14, minute=0, second=0),
        check_out=F('check_out').replace(hour=12, minute=30, second=0)
    )
 """
    import pandas as pd
    from datetime import time
    from datetime import timedelta
    from django.db import transaction
    # Supposons que vous ayez déjà un DataFrame nommé 'df' contenant vos réservations
    # avec des colonnes 'check_in' et 'check_out' de type datetime
    reservations = Reservation.objects.all()

    # Définir les nouvelles heures de check-in et check-out

    # Créer un DataFrame pandas à partir des réservations
    # Supposons que df est votre DataFrame contenant les réservations
    df = pd.DataFrame(list(reservations.values('id', 'check_in', 'check_out', 'total_price')))


    # Convertir les colonnes en datetime si elles ne le sont pas déjà
    df['check_in'] = pd.to_datetime(df['check_in'])
    df['check_out'] = pd.to_datetime(df['check_out'])

    # Définir les nouvelles heures de check-in et check-out
    check_in_time = timedelta(hours=14)  # 14:00
    check_out_time = timedelta(hours=12)  # 11:00

    # Ajuster l'heure de check-in à 14:00
    df['check_in'] = df['check_in'].dt.normalize() + check_in_time

    # Ajuster l'heure de check-out à 11:00
    df['check_out'] = df['check_out'].dt.normalize() + check_out_time

    # Calculer le nombre de jours réservés pour chaque réservation
    df['days_reserved'] = (df['check_out'] - df['check_in']).dt.total_seconds() / (24 * 3600)

    # Arrondir le nombre de jours à l'entier supérieur si nécessaire
    ## df['days_reserved'] = df['days_reserved'].ceil()

    # Afficher le résultat
    print(df[['check_in', 'check_out', 'days_reserved']])
    # 2. Sauvegarde dans la base de données
    @transaction.atomic
    def update_reservations(dataframe):
        for index, row in dataframe.iterrows():
            Reservation.objects.filter(id=row['id']).update(
                check_in=row['check_in'],
                check_out=row['check_out'],
            )

    # Appel de la fonction pour mettre à jour la base de données
    update_reservations(df)
