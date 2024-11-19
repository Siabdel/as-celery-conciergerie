
import json
from django.shortcuts import render
import pandas as pd
from django.db.models import Sum

def month_name_fr(month_number):
    months_fr = {
        1: 'Janvier', 2: 'Février', 3: 'Mars', 4: 'Avril',
        5: 'Mai', 6: 'Juin', 7: 'Juillet', 8: 'Août',
        9: 'Septembre', 10: 'Octobre', 11: 'Novembre', 12: 'Décembre'
    }
    return months_fr.get(month_number, '')

    
    
import json
import random
from datetime import datetime, timedelta
from decimal import Decimal

# Fonction pour générer une date aléatoire entre deux dates
def random_date(start, end):
    return start + timedelta(
        seconds=random.randint(0, int((end - start).total_seconds())),
    )

def create_reservation_fixtures():
    """_summary_
        Ce script Python génère des fixtures pour des réservations avec les caractéristiques suivantes :
    Les réservations sont réparties sur toutes les propriétés (de 1 à 20).
    Chaque propriété a entre 5 et 15 réservations.
    Les dates de check-in sont comprises entre le 1er mars 2024 et le 31 décembre 2024.
    La durée du séjour varie de 1 à 14 jours.
    Les prix, frais de nettoyage et frais de service sont générés aléatoirement.
    Les statuts de réservation, plateformes, et autres détails sont choisis aléatoirement.
    Les noms et emails des invités sont générés de manière simple et incrémentale.
    Les numéros de téléphone sont générés avec un format marocain.
    Certains champs comme les demandes spéciales et les notes des invités sont parfois laissés vides.
    Pour utiliser ces fixtures :
    Exécutez ce script Python pour générer le fichier reservation_fixtures.json.
    Placez le fichier généré dans le dossier approprié de votre projet Django (généralement dans un sous-dossier fixtures de votre application).
    Chargez les fixtures avec la commande :
    text
    python manage.py loaddata reservation_fixtures.json
    """
    # Paramètres
    start_date = datetime(2024, 3, 1)
    end_date = datetime(2024, 12, 31)
    properties = list(range(1, 21))  # Supposons que nous avons 20 propriétés
    platforms = ['AIRBNB', 'BOOKING', 'VRBO', 'DIRECT']
    statuses = ['PENDING', 'CONFIRMED', 'CANCELLED', 'COMPLETED']

    reservations = []
    reservation_id = 1

    for property_id in properties:
        # Générer entre 5 et 15 réservations par propriété
        num_reservations = random.randint(5, 15)
        
        for _ in range(num_reservations):
            check_in = random_date(start_date, end_date)
            check_out = check_in + timedelta(days=random.randint(1, 14))
            
            total_price = Decimal(random.uniform(50, 500)).quantize(Decimal('0.01'))
            cleaning_fee = Decimal(random.uniform(10, 50)).quantize(Decimal('0.01'))
            service_fee = Decimal(random.uniform(5, 30)).quantize(Decimal('0.01'))
            
            reservation = {
                "model": "votre_app.reservation",
                "pk": reservation_id,
                "fields": {
                    "reservation_status": random.choice(statuses),
                    "property": property_id,
                    "check_in": check_in.isoformat(),
                    "check_out": check_out.isoformat(),
                    "guest_name": f"Guest {reservation_id}",
                    "guest_email": f"guest{reservation_id}@example.com",
                    "platform": random.choice(platforms),
                    "number_of_guests": random.randint(1, 6),
                    "total_price": str(total_price),
                    "cleaning_fee": str(cleaning_fee),
                    "service_fee": str(service_fee),
                    "guest_phone": f"+212 6{random.randint(10000000, 99999999)}",
                    "special_requests": "No special requests" if random.choice([True, False]) else "",
                    "is_business_trip": random.choice([True, False]),
                    "guest_rating": random.randint(1, 5) if random.choice([True, False]) else None,
                    "cancellation_policy": "Flexible",
                    "booking_date": (check_in - timedelta(days=random.randint(1, 30))).isoformat(),
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }
            }
            
            reservations.append(reservation)
            reservation_id += 1

    # Écrire les fixtures dans un fichier JSON
    with open('reservation_fixtures.json', 'w') as f:
        json.dump(reservations, f, indent=2)

    print(f"Generated {len(reservations)} reservation fixtures.")