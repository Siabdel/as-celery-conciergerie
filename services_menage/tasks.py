
import pandas as  pd
from datetime import datetime, timedelta, timezone
from django.db.models import Q
from django.utils import timezone
from celery import shared_task
from django.db.models.signals import post_save
from django.dispatch import receiver
from schedule.models.calendars import Calendar
from services_menage import models as serv_models
from datetime import datetime
from services_menage.models import Reservation, ServiceTask, ReservationStatus, TaskTypeService
from staff.models import Employee, Service, CustomCalendar, Absence
from staff.models import CustomCalendar as Calendar



#@shared_task
# 1. faire un etat de lieu après chaque départ :
def faire_etat_des_lieu_appart(reservation_id):
    # Logique pour nettoyer la chambre
    print(f" faire_etat_des_lieu_appart apres check_out {reservation_id}")
    # Ajoutez ici la logique réelle de nettoyage

# 2. Planifiez une tâche de nettoyage après chaque départ :
#@shared_task
def service_menage_task(reservation_id):
    reservation = Reservation.objects.get(id=reservation_id)
    cleaning_time = reservation.check_out + timezone.timedelta(hours=2)
    available_employee = find_available_employee(cleaning_time)
    
    if available_employee:
        cleaning_task = ServiceTask.objects.create(
            reservation=reservation,
            employee=available_employee,
            scheduled_time=cleaning_time
        )
        
        ServiceTask.objects.create(
            start=cleaning_time,
            end=cleaning_time + timezone.timedelta(hours=2),
            title=f"Nettoy	Chambre de {reservation.client}",
            calendar=available_employee.calendar
        )
        
# 4. Planifiez de tache de check_in a l'Entrée du client, check_out après chaque départ :
#@shared_task
def service_checkin_task():
    #raise Exception("schedule_checkin_checkout ")
    ##futur_resevations = Reservation.objects.filter(start__gte=timezone.now())
    
    futur_resevations = serv_models.Reservation.objects.all()
    ## 1. Créez un calendrier principal pour les réservations :
    try :
        check_service_calendar = Calendar.objects.get(slug="calendrier-employee")
    except Exception as err :
        raise Exception("ne trouve pas Calendrier ", err)

    for reservation in futur_resevations:
        ## get calendar 
        affected__employee = find_available_employee(reservation.check_in)
        ## create Event check-in
        try :
            event_in = ServiceTask.objects.get_or_create(
                # employee a affecter apres 
                employee = affected__employee,
                start_date  = reservation.check_in,
                end_date    = reservation.check_in,
                property = reservation.property,
                status =  ReservationStatus.PENDING,
                type_service = TaskTypeService.CHECKED_IN,
                description=f"Check_in guest_name = {reservation.guest_name}, Chambre de {reservation.property}"
            )
        except Exception as err:
            raise Exception("Erreur creation ServiceTask", err)
        ## create Event check-out
        affected__employee = find_available_employee(reservation.check_out)
        try :
            event_in = ServiceTask.objects.get_or_create(
                # employee a affecter apres 
                employee = affected__employee,
                start_date  = reservation.check_in,
                end_date = reservation.check_in,
                property = reservation.property,
                status = ReservationStatus.PENDING,
                type_service =  TaskTypeService.CHECKED_OUT,
                description=f"Check_out guest_name = {reservation.guest_name}, left Chambre de {reservation.property}"
            )
        except Exception as err:
            raise Exception("Erreur creation ServiceTask CHECKOUT", err)
        
        
# 4. touvez des employees diponible
def find_available_employee(cleaning_time):
    for employee in Employee.objects.all():
            if not ServiceTask.objects.filter(
                #calendar=employee.calendar,
                Q(start_date__lte = cleaning_time) &
                Q(end_date__gte = cleaning_time)
            ).exists():
                return employee
    return None

##
def get_available_employee(year, month):
    """
    """
    employees = Employee.objects.all()
    absences = Absence.objects.filter(
      start_date__year=year,
      start_date__month=month
    )
    scheduled_tasks = ServiceTask.objects.filter(
      start_date__year=year,
      start_date__month=month
    )

    employee_df = pd.DataFrame(list(employees.values()))
    absence_df = pd.DataFrame(list(absences.values()))
    task_df = pd.DataFrame(list(scheduled_tasks.values()))
    availability = calculate_employee_availability(year, month)
    ##
    return availability.to_dict(orient='records')

def calculate_employee_availability(year, month):
    """_summary_: Cette fonction calculate_availability calcule la 
        disponibilité des employés sur une période d'un mois donné, 
        en tenant compte des absences et des tâches planifiées. 
        Voici une explication détaillée de chaque partie de la fonction :
    #------
    en se basant sur le models.py ci-joint :
    avec pandas , trouver les employee dispos pour un mois donnee en tenant compte des absences 
    , service_task programmées
    """    
    # Définir la période
    start_date = datetime(year, month, 1).date()
    end_date = (start_date.replace(day=1) + pd.offsets.MonthEnd()).to_pydatetime()
    end_date = end_date.date()

    # Récupérer tous les employés
    employees = Employee.objects.all()

    # Créer un DataFrame pour chaque jour du mois
    date_range = pd.date_range(start=start_date, end=end_date)
    availability_df = pd.DataFrame(index=employees.values_list('name', flat=True), columns=date_range)
    availability_df = availability_df.fillna(1)  # tt les dispos marquer a 1 signifie disponible

    # Marquer les indisponibilités basées sur les événements
    try :
        check_service_calendar = Calendar.objects.get(slug="calendrier-employee")
    except Exception as err :
        raise Exception("ne trouve pas Calendrier ", err)


    # Marquer les indisponibilités basées sur les tâches de service
    tasks = ServiceTask.objects.filter(
        Q(start_date__date__lte=end_date) & 
        Q(end_date__date__gte=start_date)
    )
    for task in tasks:
        if task.employee and task.employee.id:
            task_dates = pd.date_range(
                max(task.start_date.date(), start_date),
                min(task.end_date.date(), end_date)
            )
            availability_df.loc[task.employee.name, task_dates] = 0

    # Marquer les absences des employés
    absences = Absence.objects.filter(
        Q(start_date__lte=end_date) &
        Q(end_date__gte=start_date)
    )
    for absence in absences:
        absence_dates = pd.date_range(
            max(absence.start_date.date(), start_date),
            min(absence.end_date.date(), end_date)
        )
        availability_df.loc[absence.employee.name, absence_dates] = 0

    return task_dates, availability_df

#-----------------------------------------
# Fonction d'analyse de la disponibilité
#-----------------------------------------
def analyze_availability(year, month):
    availability = calculate_employee_availability(year, month)
    
    # Nombre total de jours disponibles par employé
    total_available_days = availability.sum(axis=1)
    
    # Pourcentage de disponibilité par employé
    availability_percentage = (availability.sum(axis=1) / availability.shape[1]) * 100
    
    # Jours où tous les employés sont disponibles
    all_available_days = availability[availability.sum(axis=0) == availability.shape[0]].columns
    
    # Employés les plus disponibles
    most_available_employees = Employee.objects.filter(id__in=total_available_days.nlargest(3).index)
    
    return {
        'total_available_days': total_available_days,
        'availability_percentage': availability_percentage,
        'all_available_days': all_available_days,
        'most_available_employees': most_available_employees
    }

# Utilisation
# results = analyze_availability(2024, 1)
# print(results)

def cron_update_reservation_status(reservation):
    aujourdhui = timezone.now()
    mois_encours = aujourdhui.month
    # pendre que les resa a partir du mois encours 
    reservations = Reservation.objects.filter(check_in__month = mois_encours)
    #update status tout les mois_encours
    for resa in reservations:
        update_reservation_status(resa)

def update_reservation_status(reservation):

    aujourdhui = timezone.now()

    # Si la réservation est annulée, c'est prioritaire sur tous les autres statuts
    if hasattr(reservation, 'cancelled_at') and reservation.cancelled_at is not None:
        reservation.reservation_status = ReservationStatus.CANCELLED
        return  # On arrête ici pour ne pas continuer à changer le statut

    # Grace period (période de grâce) pour certains statuts
    grace_period = timezone.timedelta(hours=2)

    # Si la réservation est "PENDING" (en attente)
    if reservation.reservation_status == ReservationStatus.PENDING:
        if aujourdhui >= (reservation.check_in + grace_period):
            reservation.reservation_status = ReservationStatus.NEEDS_ATTENTION
            # Envoyer une notification à l'équipe de gestion
            #send_notification_to_management(reservation)
        elif aujourdhui >= (reservation.check_in + timezone.timedelta(hours=24)):
            reservation.reservation_status = ReservationStatus.EXPIRED

    # Si la réservation est "CONFIRMED" (confirmée)
    elif reservation.reservation_status == ReservationStatus.CONFIRMED:
        if reservation.check_in <= aujourdhui < reservation.check_out:
            reservation.reservation_status = ReservationStatus.CHECKED_IN

    # Si la réservation est "CHECKED_IN" (en cours)
    elif reservation.reservation_status == ReservationStatus.CHECKED_IN or \
            reservation.reservation_status == ReservationStatus.IN_PROGRESS :
        if aujourdhui >= reservation.check_out:
            reservation.reservation_status = ReservationStatus.CHECKED_OUT

    # Si la réservation est "CHECKED_OUT" (terminée)
    elif reservation.reservation_status == ReservationStatus.CHECKED_OUT:
        if aujourdhui >= (reservation.check_out + timezone.timedelta(hours=24)):
            reservation.reservation_status = ReservationStatus.COMPLETED

    # Si la réservation est "IN_PROGRESS" et que la date de check-out est dépassée
    elif reservation.reservation_status == ReservationStatus.IN_PROGRESS and reservation.check_out < aujourdhui:
        reservation.reservation_status = ReservationStatus.EXPIRED
    elif not reservation.reservation_status :
        reservation.reservation_status = ReservationStatus.PENDING

    # Si le statut est "EXPIRED", on ne le change pas
    # L'expiration n'est pas réversible à ce stade.


def find_employee():
    #raise Exception("schedule_checkin_checkout ")
    ## 1. Créez un calendrier principal pour les réservations :
    try :
        check_service_calendar = Calendar.objects.get(slug="calendrier-employee")
    except Exception as err :
        raise Exception("ne trouve pas Calendrier ", err)

    
    futur_resevations = Reservation.objects.filter(start__gte=timezone.now())
    ## 1. Créez un calendrier principal pour les réservations :
    try :
        check_service_calendar = Calendar.objects.get(slug="calendrier-employee")
    except Exception as err :
        raise Exception("ne trouve pas Calendrier ", err)

    for reservation in futur_resevations:
        ## get calendar 
        affected__employee = find_available_employee(reservation.check_in)
        ## create Event check-in
        print("employee affecter ", affected__employee)
        