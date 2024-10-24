
import pandas as pd
from votre_app.models import Absence, User, Calendar  # Assurez-vous d'importer les modèles nécessaires
"""
    Explications des modifications :
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

# Créer et sauvegarder les objets Absence
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
Absence créée avec succès : Mme Marie Therez - Cleaner
Absence créée avec succès : Mme Nazha Kattani - Cleaner
Absence créée avec succès : Amoucha Nadia - Cleaner
Absence créée avec succès : Abdelaziz SADQUAOUI - Cleaner
"""