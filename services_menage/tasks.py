
import pandas as  pd
from datetime import datetime, timedelta
from django.db.models import Q
from django.utils import timezone
from celery import shared_task
from django.db.models.signals import post_save
from django.dispatch import receiver
from schedule.models.calendars import Calendar
from services_menage import models as serv_models
from .models import Employee,  ServiceTask, Reservation, Absence


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
@shared_task
def service_checkin_task():
    #raise Exception("schedule_checkin_checkout ")
    ##futur_resevations = Reservation.objects.filter(start__gte=timezone.now())
    
    futur_resevations = serv_models.Reservation.objects.all()
    ## 1. Créez un calendrier principal pour les réservations :
    check_service_calendar = Calendar.objects.get(slug="calendrier-employee")

    for reservation in futur_resevations:
        ## get calendar 
        affected__employee = find_available_employee(reservation.check_in)
        ## create Event check-in
        try :
            event_in = ServiceTask.objects.get_or_create(
                # employee a affecter apres 
                employee = affected__employee,
                start_date  = reservation.check_in,
                end_date    = reservation.check_out,
                property = reservation.property,
                status = ServiceTask.TaskStatus.PENDING,
                type_service = ServiceTask.TypeService.CHECK_IN,
                description=f"Check_in guest_name = {reservation.guest_name}, Chambre de {reservation.property}"
            )
        except Exception as err:
            pass
        ## create Event check-out
        affected__employee = find_available_employee(reservation.check_out)
        try :
            event_in = ServiceTask.objects.get_or_create(
                # employee a affecter apres 
                employee = affected__employee,
                start_date  = reservation.check_in,
                end_date = reservation.check_out,
                property = reservation.property,
                status = ServiceTask.TaskStatus.PENDING,
                type_service = ServiceTask.TypeService.CHECK_OUT,
                description=f"Check_out guest_name = {reservation.guest_name}, left Chambre de {reservation.property}"
            )
        except Exception as err:
            pass
        
        
# 4. touvez des employees diponible
def find_available_employee(cleaning_time):
    for employee in Employee.objects.all():
            if not ServiceTask.objects.filter(
                #calendar=employee.calendar,
                start_date__lte = cleaning_time,
                end_date__gte = cleaning_time
            ).exists():
                return employee
    return None

##
def get_available_emplyee(year, month):
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

"""_summary_Cette fonction calculate_availability calcule la 
    disponibilité des employés sur une période d'un mois donné, 
    en tenant compte des absences et des tâches planifiées. 
    Voici une explication détaillée de chaque partie de la fonction :

"""

"""
en se basant sur le models.py ci-joint :
avec pandas , trouver les employee dispos pour un mois donnee en tenant compte des absences 
, service_task programmées
"""    
import pandas as pd
from datetime import datetime
from django.utils import timezone
from schedule.models import Event
from .models import Employee, Reservation, ServiceTask, Absence, Property

def calculate_employee_availability(year, month):
    # Définir la période
    start_date = datetime(year, month, 1)
    end_date = (start_date.replace(day=1) + pd.offsets.MonthEnd()).to_pydatetime()

    # Récupérer tous les employés
    employees = Employee.objects.all()

    # Créer un DataFrame pour chaque jour du mois
    date_range = pd.date_range(start=start_date, end=end_date)
    availability_df = pd.DataFrame(index=employees.values_list('id', flat=True), columns=date_range)
    availability_df = availability_df.fillna(1)  # 1 signifie disponible

    # Récupérer tous les événements pour la période
    events = Event.objects.filter(
        start__date__lte=end_date.date(),
        end__date__gte=start_date.date()
    )

    # Marquer les indisponibilités basées sur les événements
    for event in events:
        employee = employees.filter(calendar=event.calendar).first()
        if employee:
            event_dates = pd.date_range(
                max(event.start.date(), start_date.date()),
                min(event.end.date(), end_date.date())
            )
            availability_df.loc[employee.id, event_dates] = 0

    # Marquer les indisponibilités basées sur les réservations
    reservations = Reservation.objects.filter(
        check_in__date__lte=end_date.date(),
        check_out__date__gte=start_date.date()
    )
    for reservation in reservations:
        reservation_dates = pd.date_range(
            max(reservation.check_in.date(), start_date.date()),
            min(reservation.check_out.date(), end_date.date())
        )
        # Supposons que tous les employés sont occupés pendant une réservation
        availability_df.loc[:, reservation_dates] = 0

    # Marquer les indisponibilités basées sur les tâches de service
    tasks = ServiceTask.objects.filter(
        start_date__date__lte=end_date.date(),
        end_date__date__gte=start_date.date()
    )
    for task in tasks:
        if task.employee_id:
            task_dates = pd.date_range(
                max(task.start_date.date(), start_date.date()),
                min(task.end_date.date(), end_date.date())
            )
            availability_df.loc[task.employee_id, task_dates] = 0

    # Marquer les absences des employés
    absences = Absence.objects.filter(
        start_date__lte=end_date.date(),
        end_date__gte=start_date.date()
    )
    for absence in absences:
        absence_dates = pd.date_range(
            max(absence.start_date, start_date.date()),
            min(absence.end_date, end_date.date())
        )
        availability_df.loc[absence.employee_id, absence_dates] = 0

    return availability_df

# Fonction d'analyse de la disponibilité
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