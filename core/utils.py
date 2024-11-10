#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import json
import random
import pandas as pd
import numpy as np
from PIL import Image
from io import BytesIO
from django.core.files import File
from django.conf import settings
from datetime import datetime, timedelta
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.timezone import make_aware, is_naive
from decimal import Decimal


"""_summary_Pandas pour l’analyse des données
Avec pandas, vous pouvez générer des rapports analytiques sur les revenus ou l'occupation des biens.
"""
def generer_rapport_revenus():
    reservations = Reservation.objects.all().values('date_debut', 'revenu')
    df = pd.DataFrame(list(reservations))
    rapport = df.groupby(df['date_debut'].dt.year)['revenu'].sum()
    return rapport

# Liste d'échantillons de noms d'invités de différentes nationalités
guests = [
    ("Emma Thompson", "emma.thompson@email.com", "+447911123456"),  # UK
    ("Juan García", "juan.garcia@email.com", "+34611223344"),  # Spain
    ("Yuki Tanaka", "yuki.tanaka@email.com", "+819012345678"),  # Japan
    ("Mohammed Al-Fayed", "mohammed.alfayed@email.com", "+971501234567"),  # UAE
    ("Olga Ivanova", "olga.ivanova@email.com", "+79161234567"),  # Russia
    ("Pierre Dubois", "pierre.dubois@email.com", "+33612345678"),  # France
    ("Li Wei", "li.wei@email.com", "+8613912345678"),  # China
    ("Maria Silva", "maria.silva@email.com", "+5511987654321"),  # Brazil
    ("Hans Müller", "hans.mueller@email.com", "+4915123456789"),  # Germany
    ("Fatima Ahmed", "fatima.ahmed@email.com", "+201234567890"),  # Egypt
    ("Giovanni Rossi", "giovanni.rossi@email.com", "+393312345678"),  # Italy
    ("Sven Andersson", "sven.andersson@email.com", "+46701234567"),  # Sweden
    ("Priya Patel", "priya.patel@email.com", "+919876543210"),  # India
    ("Kim Min-jun", "kim.minjun@email.com", "+821012345678"),  # South Korea
    ("Sophia Papadopoulos", "sophia.papadopoulos@email.com", "+306912345678"),  # Greece
    ("Alejandro Rodríguez", "alejandro.rodriguez@email.com", "+525512345678"),  # Mexico
    ("Aisha Mbeki", "aisha.mbeki@email.com", "+27823456789"),  # South Africa
    ("Nguyen Van Minh", "nguyen.vanminh@email.com", "+84912345678"),  # Vietnam
    ("Marta Kowalska", "marta.kowalska@email.com", "+48501234567"),  # Poland
    ("Ahmed Hassan", "ahmed.hassan@email.com", "+212612345678")  # Morocco
]

def generate_reservation_fixtures(num_reservations=100):
    start_date = datetime(2024, 11, 1)
    end_date = datetime(2025, 2, 28)
    current_date = datetime(2024, 10, 28)

    # Générer une série de dates pour les check-in
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    
    # Créer un DataFrame avec les dates de check-in
    df = pd.DataFrame({'check_in': date_range})
    
    # Ajouter une durée aléatoire pour chaque réservation (1 à 7 jours)
    df['duration'] = np.random.randint(1, 8, size=len(df))
    
    # Calculer les dates de check-out
    df['check_out'] = df['check_in'] + pd.to_timedelta(df['duration'], unit='D')
    
    # Sélectionner aléatoirement num_reservations lignes
    df = df.sample(n=num_reservations, replace=True).reset_index(drop=True)

    platforms = ['airbnb', 'booking', 'direct']
    statuses = ['pending', 'confirmed', 'checked_in', 'checked_out', 'cancelled']
    cancellation_policies = ['Flexible', 'Moderate', 'Strict']

    fixtures = []
    for i, row in df.iterrows():
        guest = random.choice(guests)
        booking_date = current_date - timedelta(days=random.randint(1, 30))
        if is_naive(booking_date):
            booking_date = make_aware(booking_date)

        if is_naive(current_date):
            created_at = make_aware(current_date)
        else:
            created_at = current_date
        
        total_price = Decimal(random.randint(500, 2000))
        cleaning_fee = Decimal(random.randint(30, 100))
        service_fee = Decimal(random.randint(20, 50))

        fixture = {
            "model": "votre_app.reservation",
            "pk": i + 1,
            "fields": {
                "property": random.randint(1, 5),
                "check_in": row['check_in'].isoformat() + "Z",
                "check_out": row['check_out'].isoformat() + "Z",
                "guest_name": guest[0],
                "guest_email": guest[1],
                "platform": random.choice(platforms),
                "reservation_status": random.choice(statuses),
                "number_of_guests": random.randint(1, 6),
                "total_price": str(total_price),
                "cleaning_fee": str(cleaning_fee),
                "service_fee": str(service_fee),
                "guest_phone": guest[2],
                "special_requests": f"Special request for {guest[0]}",
                "is_business_trip": random.choice([True, False]),
                "guest_rating": random.randint(1, 5) if random.random() > 0.5 else None,
                "cancellation_policy": random.choice(cancellation_policies),
                #"booking_date": (current_date - timedelta(days=random.randint(1, 30))).isoformat() + "Z",
                #"created_at": current_date.isoformat() + "Z",
                "booking_date": booking_date.isoformat(),
                "created_at": created_at.isoformat(),
                "created_by": 1
            }
        }
        fixtures.append(fixture)

    return fixtures

# Générer les fixtures
reservations = generate_reservation_fixtures(100)

# Écrire les fixtures dans un fichier JSON
with open('reservation_fixtures.json', 'w') as f:
    json.dump(reservations, f, indent=2)

print("Fixtures generated and saved to reservation_fixtures.json")



class Dict2Obj(object):
    """
    Turns a dictionary into a class
    """
    #----------------------------------------------------------------------
    def __init__(self, dictionary):
        """Constructor"""
        for key in dictionary:
            setattr(self, key, dictionary[key])



def make_thumbnail(image, size=(100, 100)):
    """Makes thumbnails of given size from given image"""

    im = Image.open(image)

    im.convert('RGB') # convert mode

    im.thumbnail(size) # resize image

    thumb_io = BytesIO() # create a BytesIO object

    im.save(thumb_io, 'JPEG', quality=85) # save image to BytesIO object

    thumbnail = File(thumb_io, name=image.name) # create a django friendly File object

    return thumbnail

##  

def process_resize_image(image, output_dir, thumbnail_size=(100, 100), large_size=(800, 600)):
    """
    Traite une images de produit en créant des miniatures de taille uniforme
    et une grande image.

    Args:
        image :  ProductImage instance
        output_dir (str): Le répertoire de sortie où les images traitées seront enregistrées.
        thumbnail_size (tuple): Taille de la miniature (largeur, hauteur). Par défaut: (100, 100).
        large_size (tuple): Taille de la grande image (largeur, hauteur). Par défaut: (800, 600).
    """

    # Ouvre l'image
    with Image.open(image.image.path) as img:
        # Crée une miniature
        thumbnail = img.copy()
        thumbnail.thumbnail(thumbnail_size)

        # Crée une grande image avec un rapport d'aspect préservé
        large_img = img.copy()
        
        # Size of the image in pixels (size of original image) 
        # (This is not mandatory) 
        width, height = large_img.size 
 
       
        # Enregistre les images traitées
        base_name = os.path.basename(image.image.path)
        thumbnail_path = os.path.join(output_dir, 
                                  f"thumbnail_{thumbnail_size[0]}x{thumbnail_size[1]}_{base_name}")
        large_path = os.path.join(output_dir,
                                  f"large_{large_size[0]}x{large_size[1]}_{base_name}")

        thumbnail.save(thumbnail_path)
        #large_img.save(large_path)
        large_img.save(large_path)

        # Retourne les chemins des images traitées
        return thumbnail_path, large_path


def process_default_image(image, output_dir, thumbnail_size=(100, 100), large_size=(800, 600)):
    """
    """
    # Ouvre l'image
    with Image.open(image.path) as img:
        # Crée une miniature
        thumbnail = img.copy()
        thumbnail.thumbnail(thumbnail_size)

        # Crée une grande image avec un rapport d'aspect préservé
        large_img = img.copy()
        large_img.thumbnail(large_size)

        # Enregistre les images traitées
        base_name = os.path.basename(image.path)
        thumbnail_path = os.path.join(output_dir, f"thumbnail_{base_name}")
        large_path = os.path.join(output_dir, f"large_{base_name}")

        thumbnail.save(thumbnail_path)
        large_img.save(large_path)

        # Retourne les chemins des images traitées
        return thumbnail_path, large_path