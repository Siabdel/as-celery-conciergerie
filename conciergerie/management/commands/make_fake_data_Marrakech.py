# your_app/management/commands/fake_maroc_ma.py
# conciergerie/management/commands/fake_maroc_ma.py
# conciergerie/management/commands/make_fake_data_Marrakech.py
import os, random, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from datetime import timedelta, datetime, time
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import IntegrityError
from faker import Faker

from core.models import ResaStatus, PlatformChoices, Agency
from conciergerie.models import Property, Reservation, PricingRule

User = get_user_model()

# --------------------  MOROCCO DATA  --------------------
VILLES = {
    "Marrakech": (31.6295, -7.9811),
    "Agadir": (30.4278, -9.5981),
}

PRENOMS_M = [
    "Youssef", "Amine", "Othmane", "Anas", "Hamza", "Reda", "Imad", "Ayoub",
    "Mehdi", "Hicham", "Said", "Khalid", "Driss", "Zakaria", "Nabil",
]

PRENOMS_F = [
    "Fatima", "Amal", "Imane", "Salma", "Sara", "Chaima", "Meryem", "Zineb",
    "Asmae", "Soukaina", "Noura", "Samira", "Kawtar", "Yasmine", "Oumaima",
]

NOMS = [
    "Alaoui", "Bennis", "Lamrani", "Fassi", "Benani", "Chakir", "El Amrani",
    "Hafidi", "Kandil", "Mansouri", "Raji", "Sabiri", "Tazi", "Naciri",
    "Benzekri", "Daoudi", "Harrouni", "El Haiti", "Amrani", "Bouzidi",
]

TYPE_BIEN = ["apartment", "house", "villa"]

PLATEFORMES = [
    (PlatformChoices.AIRBNB, "Airbnb"),
    (PlatformChoices.BOOKING, "Booking"),
    ("LOCAVACANCES", "Location-vacances.ma"),
    ("DIRECT", "Réservation directe"),
]

fake = Faker()
fake.seed_instance(42)
random.seed(42)


def _agency_for(user):
    if hasattr(user, "profile") and getattr(user.profile, "agency", None):
        return user.profile.agency
    return Agency.objects.get_or_create(name="Default Agency", slug="default")[0]


class Command(BaseCommand):
    help = "Generate ~150 Moroccan reservations (multi-agency)"

    def add_arguments(self, parser):
        parser.add_argument("--user", type=str, help="Super-user username", required=False)

    def handle(self, *args, **options):
        superuser = User.objects.filter(is_superuser=True).first()
        if options["user"]:
            superuser = User.objects.get(username=options["user"])

        agency = _agency_for(superuser)
        owners = self.create_owners(agency)
        props = self.create_properties(agency, owners)
        self.create_reservations(agency, props)
        self.stdout.write(self.style.SUCCESS(f"✅ 150 reservations created for agency «{agency}»"))

    # ----------------------------------------------------------
    def create_owners(self, agency):
        owners = []
        for i in range(15):
            genre = random.choice(["M", "F"])
            first = random.choice(PRENOMS_M if genre == "M" else PRENOMS_F)
            last = random.choice(NOMS)
            email = f"{first.lower()}.{last.lower()}@gmail.com"
            user, _ = User.objects.get_or_create(
                username=email,
                defaults=dict(first_name=first, last_name=last, email=email),
            )
            owners.append(user)
        return owners

    # ----------------------------------------------------------
    def create_properties(self, agency, owners):
        props = []
        superuser = User.objects.filter(is_superuser=True).first()

        agency = _agency_for(superuser)

        for ville, (lat, lng) in VILLES.items():
            for k in range(7 if ville == "Marrakech" else 8):
                prop, _ = Property.objects.get_or_create(
                    agency=agency,
                    name=f"{ville} – {fake.street_address()}",
                    defaults=dict(
                        owner=random.choice(owners),
                        type=random.choice(TYPE_BIEN),
                        address=f"{fake.building_number()} {fake.street_name()}, {ville}",
                        latitude=lat + random.uniform(-0.02, 0.02),
                        longitude=lng + random.uniform(-0.02, 0.02),
                        price_per_night=Decimal(random.randint(350, 1400)),  # MAD
                    ),
                )
                self.create_pricing_rules(prop)
                props.append(prop)
        return props

    # ----------------------------------------------------------
    def create_pricing_rules(self, prop):
        today = timezone.now().date()
        for _ in range(random.randint(1, 3)):
            start = today + timedelta(days=random.randint(0, 365))
            end   = start + timedelta(days=random.randint(15, 90))
            PricingRule.objects.get_or_create(
                agency=prop.agency,          # ← obligatoire
                property=prop,
                start_date=start,
                end_date=end,
                defaults=dict(
                    price_per_night=prop.price_per_night + Decimal(random.randint(-100, 200)),
                    is_active=True,
                    priority=random.randint(0, 5),
                    min_nights=random.randint(1, 4),
                ),
            )

    # ----------------------------------------------------------
    def create_reservations(self, agency, props):
        today = timezone.now().date()
        created = 0
        while created < 150:
            prop = random.choice(props)
            check_in_date = today + timedelta(days=random.randint(0, 365))
            duration = random.randint(1, 10)
            check_out_date = check_in_date + timedelta(days=duration)

            now_dt = timezone.now()
            check_in_dt = timezone.make_aware(datetime.combine(check_in_date, time(14, 0)))
            check_out_dt = timezone.make_aware(datetime.combine(check_out_date, time(12, 0)))

            # coherent status
            if check_out_dt < now_dt:
                status = random.choice([ResaStatus.COMPLETED, ResaStatus.CHECKED_OUT])
            elif check_in_dt <= now_dt <= check_out_dt:
                status = random.choice([ResaStatus.CHECKED_IN, ResaStatus.IN_PROGRESS])
            elif check_in_dt <= now_dt + timedelta(days=7):
                status = random.choice([ResaStatus.CONFIRMED, ResaStatus.NEEDS_ATTENTION])
            else:
                status = ResaStatus.PENDING

            total = prop.get_price_for_date(check_in_date) * duration

            try:
                Reservation.objects.create(
                    agency=agency,
                    property=prop,
                    check_in=check_in_dt,
                    check_out=check_out_dt,
                    guest_name=f"{random.choice(PRENOMS_M + PRENOMS_F)} {random.choice(NOMS)}",
                    guest_email=fake.email(),
                    platform=random.choice(PLATEFORMES)[0],
                    number_of_guests=random.randint(1, 6),
                    total_price=total,
                    cleaning_fee=Decimal(random.randint(100, 400)),
                    service_fee=Decimal(random.randint(20, 150)),
                    reservation_status=status,
                )
                created += 1
            except IntegrityError:
                continue  # duplicate slot