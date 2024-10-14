import json
import pandas as pd
from datetime import datetime, timedelta
from django.shortcuts import render, HttpResponse
from django.utils import timezone
from django.db.models.signals import post_save
from schedule.models.calendars import Calendar
from schedule.models import Event
from services_menage.models import  Calendar, Absence
from services_menage import models as serv_models
from django.utils.timezone import now
from django_celery_beat.models import PeriodicTask, IntervalSchedule
from collections import defaultdict


def home(request):
    return render(request, "home_page.html")

## Calendar reservations
def calendar_reservation(request):
    return render(request, 'fullcalendar_resa.html')

## Calendar reservations
def calendar_employee(request):
    return render(request, 'fullcalendar_emp.html')

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




"""
Pour calculer les dates de disponibilité d'un employé pour un mois donné, nous devons vérifier les absences enregistrées dans la base de données pour cet employé et en déduire les jours où il est disponible.

Voici les étapes principales :

Obtenir tous les jours du mois spécifié.
Obtenir les absences de l'employé pendant ce mois.
Déduire les jours disponibles en excluant les jours où l'employé est absent.
"""

def get_employee_availability_for_month(employee, year, month):
    # Générer toutes les dates du mois donné
    aujourdhui = datetime.now()
    start_date = datetime(year, month, 1)
    next_month = start_date.replace(day=28) + timedelta(days=4)  # Aller au mois suivant
    end_date = next_month - timedelta(days=next_month.day)  # Dernier jour du mois

    all_days_in_month = pd.date_range(start=start_date, end=end_date).to_pydatetime().tolist()
    all_days_in_month = [day.date() for day in all_days_in_month]

    # Récupérer toutes les absences de l'employé pour le mois spécifié
    absences = serv_models.Absence.objects.filter(
        employee=employee,
        start_date__lte=end_date,
        end_date__gte=start_date
    )

    # Récupérer toutes les tâches de l'employé pour le mois spécifié
    tasks = serv_models.ServiceTask.objects.filter(
        employee=employee,
        start_date__date__lte=end_date,
        end_date__date__gte=start_date
    )

    # Liste des jours où l'employé est absent
    absent_days = []
    for absence in absences:
        absence_days = pd.date_range(start=absence.start_date, end=absence.end_date).to_pydatetime().tolist()
        absent_days.extend(absence_days)

    # Liste des jours où l'employé a des tâches programmées
    task_days = []
    for task in tasks:
        task_days_range = pd.date_range(start=task.start_date, end=task.end_date).to_pydatetime().tolist()
        task_days.extend(task_days_range)

    # Retirer les jours d'absence et les jours avec tâches des jours du mois
    unavailable_days = set([day.date() for day in absent_days] + [day.date() for day in task_days])
    available_days = [day for day in all_days_in_month if day  not in unavailable_days]
    available_days = [day for day in available_days if day > aujourdhui.date()]

    return available_days

"""
Plan de la fonction d'affectation :

1-Récupérer les réservations pour un mois donné.
2-Pour chaque réservation :
3-Générer une tâche de check-in à la date de début de la réservation.
4-Générer une tâche de check-out à la date de fin de la réservation.
5-Générer une tâche de ménage après le check-out.
6-Affecter des employés disponibles pour ces tâches en excluant les jours d'absence et les autres tâches déjà assignées.
""" 


def assign_tasks_from_reservations_with_balancing(year, month):
    """
    Fonction pour affecter automatiquement des employés aux tâches de check-in, check-out et ménage
    en fonction des réservations des clients, avec équilibrage des tâches.

    Parameters:
        year (int): Année pour laquelle affecter les tâches.
        month (int): Mois pour lequel affecter les tâches.
    """
    
    # Récupérer les réservations pour le mois donné
    reservations = serv_models.Reservation.objects.filter(
        check_in__year=year, check_in__month=month
    )

    # Obtenir la liste de tous les employés
    employees = serv_models.Employee.objects.all()

    # Créer un dictionnaire pour suivre le nombre de tâches de chaque employé
    task_count = defaultdict(int)  # Par défaut, chaque employé a 0 tâche

    # Pré-remplir le nombre de tâches déjà assignées pour le mois donné
    for employee in employees:
        task_count[employee.id] = serv_models.ServiceTask.objects.filter(
            employee=employee,
            start_date__year=year,
            start_date__month=month
        ).count()

    # Stocker les tâches affectées
    assigned_tasks = []

    # Fonction pour trouver l'employé avec le moins de tâches disponible pour une date donnée
    def find_employee_for_task(date):
        available_employees = []
        for employee in employees:
            available_days = get_employee_availability_for_month(employee, year, month)
            if date in [day  for day in available_days]:
                available_employees.append(employee)

        if not available_employees:
            return None

        # Trier les employés par le nombre de tâches déjà affectées
        available_employees.sort(key=lambda emp: task_count[emp.id])

        return available_employees[0]  # Retourner l'employé avec le moins de tâches
    ## ---------------------
    ## create task default
    ## ---------------------
    def create_task_default(reservation):
        task = serv_models.ServiceTask.objects.create(
            reservation=reservation,
            employee=None,
            description=f"Erreur Impossible d'assigner un employé pour le check-in à {reservation.check_in}",
            type_service="ERROR",
            start_date=reservation.check_in,
            end_date=reservation.check_out + timedelta(hours=1),
            property=reservation.property, # Associer la tâche à la réservation
        )
        return task
    
    # Parcourir toutes les réservations pour générer les tâches
    for reservation in reservations:
        check_in_time = reservation.check_in
        check_out_time = reservation.check_out
        cleaning_day = check_out_time + timedelta(days=1)  # On fait le ménage le lendemain du check-out
        property=reservation.property, # Associer la tâche à la réservation

        # Priorité 1 : Affecter la tâche de check-in
        employee_for_check_in = find_employee_for_task(check_in_time.date())
        if employee_for_check_in:
            task = serv_models.ServiceTask.objects.create(
                employee=employee_for_check_in,
                type_service="CKIN",
                description=f"Check_in",
                start_date=check_in_time,
                end_date=check_in_time + timedelta(hours=1),
                reservation=reservation,
                property=reservation.property, # Associer la tâche à la réservation
            )
            assigned_tasks.append(task)
            task_count[employee_for_check_in.id] += 1  # Augmenter le nombre de tâches de cet employé
        else:
            create_task_default(reservation)
            print(f"Impossible d'assigner un employé pour le check-in à {check_in_time}")
        # Priorité 2 : Affecter la tâche de check-out
        employee_for_check_out = find_employee_for_task(check_out_time.date())
        if employee_for_check_out:
            task = serv_models.ServiceTask.objects.create(
                employee=employee_for_check_out,
                description=f"Check_out",
                type_service="CKOUT",
                start_date=check_out_time,
                end_date=check_out_time + timedelta(hours=1),
                reservation=reservation,
                property=reservation.property, # Associer la tâche à la réservation
            )
            assigned_tasks.append(task)
            task_count[employee_for_check_out.id] += 1  # Augmenter le nombre de tâches de cet employé
        else:
            create_task_default(reservation)
            print(f"Impossible d'assigner un employé pour le check out à {check_out_time}")

        # Priorité 3 : Affecter la tâche de ménage après le check-out
        employee_for_cleaning = find_employee_for_task(cleaning_day.date())
        if employee_for_cleaning:
            task = serv_models.ServiceTask.objects.create(
                employee=employee_for_cleaning,
                description=f"Ménage ",
                type_service="CLEAN",
                start_date=datetime.combine(cleaning_day, datetime.min.time()),
                end_date=datetime.combine(cleaning_day, datetime.min.time()) + timedelta(hours=2),
                reservation=reservation,
                property=reservation.property, # Associer la tâche à la réservation
            )
            assigned_tasks.append(task)
            task_count[employee_for_cleaning.id] += 1  # Augmenter le nombre de tâches de cet employé
        else:
            create_task_default(reservation)
            print(f"Impossible d'assigner un employé pour le ménage le {cleaning_day}")

    return assigned_tasks
