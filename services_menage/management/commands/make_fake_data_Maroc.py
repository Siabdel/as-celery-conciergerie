# your_app/management/commands/fake_maroc.py
import random
from datetime import timedelta, datetime, time
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import IntegrityError
from faker import Faker
import pandas as pd

from core.models import ReservationStatus, PlatformChoices
from services_menage.models import Property, Reservation, PricingRule

User = get_user_model()

# ------------------------------------------------------------------
# Données réalistes Maroc
# ------------------------------------------------------------------
VILLES_COORD = {
    "Casablanca": (33.5731, -7.5898),
    "Rabat": (34.0209, -6.8416),
    "Tanger": (35.7595, -5.8340),
    "Marrakech": (31.6295, -7.9811),
    "Agadir": (30.4278, -9.5981),
    "Fès": (34.0331, -5.0003),
    "Meknès": (33.8938, -5.5544),
    "Oujda": (34.6894, -1.9128),
    "Tétouan": (35.5889, -5.3626),
    "Essaouira": (31.5088, -9.7693),
    "El Jadida": (33.2319, -8.5067),
    "Safi": (32.2889, -9.2333),
    "Mohammedia": (33.6870, -7.3805),
    "Kénitra": (34.2540, -6.5897),
    "Béni Mellal": (32.3424, -6.3758),
}

PLATFORMS_LOCAL = [
    (PlatformChoices.AIRBNB, "Airbnb"),
    (PlatformChoices.BOOKING, "Booking"),
    ("WEGO", "Wego.ma"),
    ("LOCAVACANCES", "Location-vacances.ma"),
    ("DIRECT", "Réservation directe"),
]

TYPE_CHOICES = ["apartment", "house", "villa"]

fake = Faker()
fake.seed_instance(42)
random.seed(42)

# ------------------------------------------------------------------
def _random_date(start, end):
    delta = end - start
    return start + timedelta(days=random.randint(0, delta.days))


# ------------------------------------------------------------------
class Command(BaseCommand):
    help = "Génère des données fictives réalistes pour le Maroc"

    def handle(self, *args, **options):
        owners = self.create_owners()
        props = self.create_properties(owners)
        self.create_reservations(props)
        self.stdout.write(self.style.SUCCESS("✅ Données marocaines créées !"))

    # ----------------------------------------------------------
    def create_owners(self):
        owners = []
        for i in range(15):
            first = fake.first_name()
            last = fake.last_name()
            email = f"{first.lower()}.{last.lower()}@gmail.com"
            user, _ = User.objects.get_or_create(
                username=email,
                defaults=dict(
                    first_name=first,
                    last_name=last,
                    email=email,
                ),
            )
            owners.append(user)
        return owners

    # ----------------------------------------------------------
    def create_properties(self, owners):
        props = []
        for ville, (lat, lng) in VILLES_COORD.items():
            for _ in range(random.randint(1, 3)):  # 1-3 biens par ville
                prop, _ = Property.objects.get_or_create(
                    name=f"{ville} {fake.street_address()}",
                    defaults=dict(
                        owner=random.choice(owners),
                        type=random.choice(TYPE_CHOICES),
                        address=f"{fake.building_number()} {fake.street_name()}, {ville}",
                        latitude=lat + random.uniform(-0.03, 0.03),
                        longitude=lng + random.uniform(-0.03, 0.03),
                        price_per_night=Decimal(random.randint(300, 1500)),  # MAD
                    ),
                )
                self.create_pricing_rules(prop)
                props.append(prop)
        return props

    # ----------------------------------------------------------
    def create_pricing_rules(self, prop):
        today = timezone.now().date()
        for _ in range(random.randint(1, 3)):
            start = _random_date(today, today.replace(year=today.year + 1))
            end = _random_date(start, (start + timedelta(days=60)))
            PricingRule.objects.get_or_create(
                property=prop,
                start_date=start,
                end_date=end,
                defaults=dict(
                    price_per_night=prop.price_per_night
                    + Decimal(random.randint(-100, 200)),
                    is_active=True,
                    priority=random.randint(0, 5),
                    min_nights=random.randint(1, 4),
                ),
            )

    # ----------------------------------------------------------
    def create_reservations(self, props):
        today = timezone.now().date()
        for _ in range(100):
            prop = random.choice(props)
            check_in_date = _random_date(today, today.replace(year=today.year + 1))
            duration = random.randint(1, 10)
            check_out_date = check_in_date + timedelta(days=duration)

            now_dt = timezone.now()
            check_in_dt = timezone.make_aware(
                datetime.combine(check_in_date, time(14, 0))
            )
            check_out_dt = timezone.make_aware(
                datetime.combine(check_out_date, time(12, 0))
            )

            # statut cohérent
            if check_out_dt < now_dt:
                status = random.choice([ReservationStatus.COMPLETED, ReservationStatus.CHECKED_OUT])
            elif check_in_dt <= now_dt <= check_out_dt:
                status = random.choice([ReservationStatus.CHECKED_IN, ReservationStatus.IN_PROGRESS])
            elif check_in_dt <= now_dt + timedelta(days=7):
                status = random.choice([ReservationStatus.CONFIRMED, ReservationStatus.NEEDS_ATTENTION])
            else:
                status = ReservationStatus.PENDING

            total = prop.get_price_for_date(check_in_date) * duration

            try:
                Reservation.objects.create(
                    property=prop,
                    check_in=check_in_dt,
                    check_out=check_out_dt,
                    guest_name=fake.name(),
                    guest_email=fake.email(),
                    platform=random.choice(PLATFORMS_LOCAL)[0],
                    number_of_guests=random.randint(1, 6),
                    total_price=total,
                    cleaning_fee=Decimal(random.randint(100, 400)),
                    service_fee=Decimal(random.randint(20, 150)),
                    reservation_status=status,
                )
            except IntegrityError:
                continue  # doublon → on passe