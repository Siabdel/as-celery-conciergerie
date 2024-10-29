
import pandas as pd
import pandas as pd
from datetime import datetime, timedelta
from .models import Absence

from staff.models import Absence, User, Calendar  # Assurez-vous d'importer les modèles nécessaires

"""
## Explications des modifications :
    abs_df = pd.read_json("data/employees.json") : Nous gardons le DataFrame dans une variable.
    abs_list = abs_df.to_dict('records') : Nous convertissons le DataFrame en une liste de dictionnaires. Chaque dictionnaire représente une ligne du DataFrame.
    Nous itérons sur abs_list au lieu de abs.to_dict().
    Nous utilisons **elem pour décompresser le dictionnaire et passer ses clés-valeurs comme arguments nommés au constructeur d'Absence.
    Nous avons ajouté une gestion des exceptions pour capturer et afficher les erreurs potentielles lors de la création des objets Absence.
    Nous imprimons un message de succès pour chaque Absence créée.
    Assurez-vous que :
    Les noms des colonnes dans votre fichier JSON correspondent exactement aux noms des champs dans votre modèle Absence.
    Votre modèle Absence est correctement défini et importé.
    Vous exécutez ce code dans un environnement Django approprié (par exemple, dans un shell Django ou dans une commande de gestion).
    Si certains champs de votre modèle Absence ne correspondent pas exactement aux colonnes de votre fichier JSON, vous devrez peut-être faire un mappage manuel des données avant de créer l'objet Absence.
"""

# Lire le fichier JSON
# Lire le fichier JSON
abs_df = pd.read_json("data/employees.json")

# Convertir le DataFrame en liste de dictionnaires
abs_list = abs_df.to_dict('records')

# Importer des enregistrement Absence a partir dun fichier 
for elem in abs_list:
    try :
    
        # Récupérer l'utilisateur associé
        user = User.objects.get(id=elem['user'])

        # Récupérer ou créer le calendrier
        calendar_data = elem['calendar']
        calendar, created = Calendar.objects.get_or_create(
            id=calendar_data['id'],
            defaults={
                'name': calendar_data['name'],
                'slug': calendar_data['slug']
            }
        )

        # Créer une instance d'Absence avec les données
        employee = Employee(
            id=elem['id'],
            name=elem['name'],
            user=user,
            phone_number=elem['phone_number'],
            calendar=calendar,
            hire_date = timezone.now()
        )
        employee.save()
        print(f"Absence créée avec succès : {employee}")
    except Exception as err :
        print(f"Erreur", err )


"""
1. **Obtenir toutes les dates du mois :**
   - `pd.date_range()` génère une liste de toutes les dates entre le début et la fin du mois donné.
2. **Récupérer les absences de l'employé :**
   - La requête `Absence.objects.filter()` permet de sélectionner toutes les absences de l'employé dont la période chevauche le mois spécifié.
3. **Calculer les jours d'absence :**
   - Pour chaque absence, on utilise `pd.date_range()` pour obtenir les jours exacts durant lesquels l'employé est absent, que l'on stocke dans la liste `absent_days`.
4. **Exclure les jours d'absence :**
   - Enfin, on compare tous les jours du mois avec les jours d'absence et on retourne uniquement les jours où l'employé est disponible.

### Utilisation :
employee = Employee.objects.get(id=employee_id)
available_days = get_employee_availability_for_month(employee, 2024, 10)

# Afficher les jours disponibles
for day in available_days:
    print(day.strftime('%Y-%m-%d'))
"""
import pandas as pd
from datetime import datetime, timedelta
from .models import Absence


def get_employee_availability_for_month(employee, year, month):
    # Générer toutes les dates du mois donné
    start_date = datetime(year, month, 1)
    next_month = start_date.replace(day=28) + timedelta(days=4)  # S'assure d'aller au mois suivant
    end_date = next_month - timedelta(days=next_month.day)  # Dernier jour du mois

    all_days_in_month = pd.date_range(start=start_date, end=end_date).to_pydatetime().tolist()

    # Récupérer toutes les absences de l'employé pour le mois spécifié
    absences = Absence.objects.filter(
        employee=employee,
        start_date__lte=end_date,
        end_date__gte=start_date
    )

    # Liste des jours où l'employé est absent
    absent_days = []
    for absence in absences:
        absence_days = pd.date_range(start=absence.start_date, end=absence.end_date).to_pydatetime().tolist()
        absent_days.extend(absence_days)

    # Retirer les jours d'absence des jours du mois
    available_days = [day for day in all_days_in_month if day.date() not in [abs_day.date() for abs_day in absent_days]]

    return available_days


"""_summary_Explication :
Obtenir toutes les dates du mois :

pd.date_range() génère une liste de toutes les dates entre le début et la fin du mois donné.
Récupérer les absences de l'employé :

La requête Absence.objects.filter() permet de sélectionner toutes les absences de l'employé dont la période chevauche le mois spécifié.
Calculer les jours d'absence :

Pour chaque absence, on utilise pd.date_range() pour obtenir les jours exacts durant lesquels l'employé est absent, que l'on stocke dans la liste absent_days.
Exclure les jours d'absence :

Enfin, on compare tous les jours du mois avec les jours d'absence et on retourne uniquement les jours où l'employé est disponible.
Utilisation :
Si vous avez un objet Employee (par exemple avec l'ID employee_id), vous pouvez calculer la disponibilité pour un mois donné, par exemple octobre 2024 :

Récupération des tâches de l'employé :

En plus des absences, on récupère les tâches de l'employé pendant la période spécifiée grâce à la requête Task.objects.filter().
Exclure les jours où des tâches sont programmées :

De la même manière que pour les absences, nous générons une liste des jours où l'employé a des tâches programmées et les ajoutons à la liste task_days.
Exclusion des jours d'absence et de tâche :

Nous combinons les jours d'absence et les jours avec des tâches en utilisant un ensemble (set()) pour éviter les doublons. Ensuite, nous filtrons la liste des jours disponibles en excluant ceux qui apparaissent dans l'ensemble des jours non disponibles.

python
Copier le code
employee = Employee.objects.get(id=employee_id)
available_days = get_employee_availability_for_month(employee, 2024, 10)

# Afficher les jours disponibles
for day in available_days:
    print(day.strftime('%Y-%m-%d'))
"""



def get_employee_availability_for_month(employee, year, month):
    # Générer toutes les dates du mois donné
    start_date = datetime(year, month, 1)
    next_month = start_date.replace(day=28) + timedelta(days=4)  # Aller au mois suivant
    end_date = next_month - timedelta(days=next_month.day)  # Dernier jour du mois

    all_days_in_month = pd.date_range(start=start_date, end=end_date).to_pydatetime().tolist()

    # Récupérer toutes les absences de l'employé pour le mois spécifié
    absences = Absence.objects.filter(
        employee=employee,
        start_date__lte=end_date,
        end_date__gte=start_date
    )

    # Récupérer toutes les tâches de l'employé pour le mois spécifié
    tasks = Task.objects.filter(
        employee=employee,
        start_time__date__lte=end_date,
        end_time__date__gte=start_date
    )

    # Liste des jours où l'employé est absent
    absent_days = []
    for absence in absences:
        absence_days = pd.date_range(start=absence.start_date, end=absence.end_date).to_pydatetime().tolist()
        absent_days.extend(absence_days)

    # Liste des jours où l'employé a des tâches programmées
    task_days = []
    for task in tasks:
        task_days_range = pd.date_range(start=task.start_time, end=task.end_time).to_pydatetime().tolist()
        task_days.extend(task_days_range)

    # Retirer les jours d'absence et les jours avec tâches des jours du mois
    unavailable_days = set([day.date() for day in absent_days] + [day.date() for day in task_days])
    available_days = [day for day in all_days_in_month if day.date() not in unavailable_days]

    return available_days


from datetime import timedelta

def assign_tasks_for_hotel_operations(year, month, check_in_times, check_out_times, cleaning_days):
    """
    Fonction pour affecter automatiquement des employés aux tâches de check-in, check-out et ménage.
    
    Parameters:
        year (int): Année pour laquelle affecter les tâches.
        month (int): Mois pour lequel affecter les tâches.
        check_in_times (list): Liste de tuples (datetime) pour les moments de check-in.
        check_out_times (list): Liste de tuples (datetime) pour les moments de check-out.
        cleaning_days (list): Liste des jours (date) où le ménage est nécessaire.
    """
    
    # Obtenir la liste de tous les employés
    employees = Employee.objects.all()
    
    # Stocker les tâches affectées
    assigned_tasks = []
    
    # Priorité 1 : Affecter les tâches de check-in
    for check_in_time in check_in_times:
        assigned = False
        for employee in employees:
            # Obtenir les jours disponibles pour cet employé
            available_days = get_employee_availability_for_month(employee, year, month)
            
            # Vérifier si l'employé est disponible au moment du check-in
            if check_in_time.date() in [day.date() for day in available_days]:
                # Créer et assigner la tâche de check-in
                task = Task.objects.create(
                    employee=employee,
                    task_description="Check-in",
                    start_time=check_in_time,
                    end_time=check_in_time + timedelta(hours=1)  # On suppose une durée d'1 heure pour un check-in
                )
                assigned_tasks.append(task)
                assigned = True
                break  # Sortir de la boucle dès qu'un employé est affecté

        if not assigned:
            print(f"Impossible d'assigner un employé pour le check-in à {check_in_time}")

    # Priorité 2 : Affecter les tâches de check-out
    for check_out_time in check_out_times:
        assigned = False
        for employee in employees:
            # Obtenir les jours disponibles pour cet employé
            available_days = get_employee_availability_for_month(employee, year, month)
            
            # Vérifier si l'employé est disponible au moment du check-out
            if check_out_time.date() in [day.date() for day in available_days]:
                # Créer et assigner la tâche de check-out
                task = Task.objects.create(
                    employee=employee,
                    task_description="Check-out",
                    start_time=check_out_time,
                    end_time=check_out_time + timedelta(hours=1)  # On suppose une durée d'1 heure pour un check-out
                )
                assigned_tasks.append(task)
                assigned = True
                break

        if not assigned:
            print(f"Impossible d'assigner un employé pour le check-out à {check_out_time}")

    # Priorité 3 : Affecter les tâches de ménage
    for cleaning_day in cleaning_days:
        assigned = False
        for employee in employees:
            # Obtenir les jours disponibles pour cet employé
            available_days = get_employee_availability_for_month(employee, year, month)
            
            # Vérifier si l'employé est disponible ce jour-là pour faire le ménage
            if cleaning_day in [day.date() for day in available_days]:
                # Créer et assigner la tâche de ménage
                task = Task.objects.create(
                    employee=employee,
                    task_description="Ménage",
                    start_time=datetime.combine(cleaning_day, datetime.min.time()),  # Début de la journée
                    end_time=datetime.combine(cleaning_day, datetime.min.time()) + timedelta(hours=2)  # On suppose 2h pour le ménage
                )
                assigned_tasks.append(task)
                assigned = True
                break

        if not assigned:
            print(f"Impossible d'assigner un employé pour le ménage le {cleaning_day}")

    return assigned_tasks

"""
    Explication de la fonction :
Paramètres :

year et month : L'année et le mois pour lesquels on affecte les tâches.
check_in_times : Une liste de datetime représentant les heures de check-in (par exemple, une liste de datetime pour chaque check-in prévu).
check_out_times : Une liste de datetime représentant les heures de check-out.
cleaning_days : Une liste de dates où le ménage doit être effectué.
Processus :

Check-in : Pour chaque check-in, on parcourt les employés et vérifie s'ils sont disponibles ce jour-là. Si oui, on assigne la tâche.
Check-out : Même logique que pour le check-in, mais pour les check-outs.
Ménage : Pour chaque jour de ménage, on assigne un employé disponible pour effectuer cette tâche.
Durée des tâches :

Les check-in et check-out sont estimés à durer 1 heure.
Le ménage est estimé à durer 2 heures par jour.
Ces durées peuvent être ajustées en fonction des besoins.
Utilisation de la fonction :
Supposons que vous ayez des moments de check-in, check-out et des jours de ménage pour un hôtel en octobre 2024. Vous pourriez utiliser cette fonction comme suit :

python
Copier le code
check_in_times = [
    datetime(2024, 10, 1, 14, 0),  # Check-in prévu le 1er octobre à 14h00
    datetime(2024, 10, 5, 15, 0),  # Check-in prévu le 5 octobre à 15h00
    # Autres moments de check-in
]

check_out_times = [
    datetime(2024, 10, 2, 11, 0),  # Check-out prévu le 2 octobre à 11h00
    datetime(2024, 10, 6, 11, 0),  # Check-out prévu le 6 octobre à 11h00
    # Autres moments de check-out
]

cleaning_days = [
    datetime(2024, 10, 3).date(),  # Ménage prévu le 3 octobre
    datetime(2024, 10, 7).date(),  # Ménage prévu le 7 octobre
    # Autres jours de ménage
]

# Appel de la fonction pour affecter automatiquement les tâches
tasks_assigned = assign_tasks_for_hotel_operations(2024, 10, check_in_times, check_out_times, cleaning_days)

# Affichage des tâches assignées
for task in tasks_assigned:
    print(f"Tâche: {task.task_description} assignée à {task.employee} le {task.start_time}")

"""