import json
import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from services_menage.models import Property

User = get_user_model()

class Command(BaseCommand):
    help = 'Generate Property fixtures'

    def handle(self, *args, **options):
        # Récupérer ou créer un utilisateur pour le propriétaire
        user, created = User.objects.get_or_create(username='owner', defaults={'email': 'owner@example.com'})

        # Liste de noms de propriétés
        property_names = [
            "Sunset Villa", "Ocean View Apartment", "Mountain Retreat", 
            "City Center Loft", "Lakeside Cottage", "Desert Oasis", 
            "Forest Cabin", "Beachfront Bungalow", "Skyline Penthouse", 
            "Countryside Farmhouse"
        ]

        # Types de propriétés
        property_types = ['apartment', 'house', 'villa']

        # Adresses fictives
        addresses = [
            "123 Seaside Ave, Beach City", "456 Mountain Rd, Highland Town",
            "789 Downtown St, Metropolis", "101 Lake Lane, Waterfront",
            "202 Desert Dr, Oasis Springs", "303 Forest Path, Woodland",
            "404 Sandy Beach Rd, Coastal Village", "505 Skyscraper Blvd, Big City",
            "606 Rural Route, Farmville", "707 Suburban St, Pleasantville"
        ]

        fixtures = []
        for i in range(10):
            price_per_night = Decimal(random.uniform(50, 500)).quantize(Decimal('0.01'))
            
            fixture = {
                "model": "services_menage.property",
                "pk": i + 1,
                "fields": {
                    "name": property_names[i],
                    "type": random.choice(property_types),
                    "address": addresses[i],
                    "owner": user.id,
                    "price_per_night": str(price_per_night),
                    "created_at": timezone.now().isoformat(),
                    "created_by": user.id,
                }
            }
            fixtures.append(fixture)

        # Écrire les fixtures dans un fichier JSON
        with open('property_fixtures.json', 'w') as f:
            json.dump(fixtures, f, indent=2)

        self.stdout.write(self.style.SUCCESS('Property fixtures generated and saved to property_fixtures.json'))
