import json
import random
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from django.utils.timezone import make_aware, is_naive
from django.core.serializers.json import DjangoJSONEncoder
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from services_menage.models import Property, Reservation
from django.db.models import Min, Max


class Command(BaseCommand):
    help = 'Generate reservation fixtures'

    def handle(self, *args, **options):
        property_ids = list(Property.objects.values_list('id', flat=True))
        
        if not property_ids:
            self.stdout.write(self.style.ERROR('No properties found in the database. Please create some properties first.'))
            return

        guests = [
            ("Emma Thompson", "emma.thompson@email.com", "+447911123456"),
            ("Juan García", "juan.garcia@email.com", "+34611223344"),
            # ... (autres invités)
        ]

        def generate_reservation_fixtures(num_reservations=100):
            start_date = datetime(2024, 11, 1)
            end_date = datetime(2025, 2, 28)
            current_date = timezone.now()

            reservations = []
            property_reservations = {pid: [] for pid in property_ids}

            while len(reservations) < num_reservations:
                property_id = random.choice(property_ids)
                check_in = start_date + timedelta(days=random.randint(0, (end_date - start_date).days))
                duration = random.randint(1, 7)
                check_out = check_in + timedelta(days=duration)

                # Vérifier les chevauchements
                overlap = False
                for existing_res in property_reservations[property_id]:
                    if (check_in < existing_res['check_out'] and check_out > existing_res['check_in']):
                        overlap = True
                        break

                if not overlap:
                    guest = random.choice(guests)
                    total_price = Decimal(random.randint(500, 2000))
                    cleaning_fee = Decimal(random.randint(30, 100))
                    service_fee = Decimal(random.randint(20, 50))

                    reservation = {
                        "model": "services_menage.reservation",
                        "pk": len(reservations) + 1,
                        "fields": {
                            "property": property_id,
                            "check_in": check_in.isoformat(),
                            "check_out": check_out.isoformat(),
                            "guest_name": guest[0],
                            "guest_email": guest[1],
                            "platform": random.choice(['airbnb', 'booking', 'direct']),
                            "reservation_status": random.choice(['pending', 'confirmed', 'checked_in', 'checked_out', 'cancelled']),
                            "number_of_guests": random.randint(1, 6),
                            "total_price": str(total_price),
                            "cleaning_fee": str(cleaning_fee),
                            "service_fee": str(service_fee),
                            "guest_phone": guest[2],
                            "special_requests": f"Special request for {guest[0]}",
                            "is_business_trip": random.choice([True, False]),
                            "guest_rating": random.randint(1, 5) if random.random() > 0.5 else None,
                            "cancellation_policy": random.choice(['Flexible', 'Moderate', 'Strict']),
                            "booking_date": (current_date - timedelta(days=random.randint(1, 30))).isoformat(),
                            "created_at": current_date.isoformat(),
                            "created_by": 1
                        }
                    }
                    reservations.append(reservation)
                    property_reservations[property_id].append({
                        'check_in': check_in,
                        'check_out': check_out
                    })

            return reservations

        # Générer les fixtures
        reservations = generate_reservation_fixtures(100)

        # Écrire les fixtures dans un fichier JSON
        with open('reservation_fixtures.json', 'w') as f:
            json.dump(reservations, f, indent=2, cls=DjangoJSONEncoder)

        self.stdout.write(self.style.SUCCESS('Fixtures generated and saved to reservation_fixtures.json'))