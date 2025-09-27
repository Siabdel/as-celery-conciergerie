# your_app/management/commands/fake_staff_ma.py
# conciergerie/management/commands/fake_staff_ma.py
# conciergerie/management/commands/make_staff_ma.py
import random
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from faker import Faker

from staff.models import Employee, Absence, Service
from core.models import CustomCalendar, Agency
from conciergerie.models import Property

User = get_user_model()

# --------------------  MOROCCO DATA  --------------------
CITIES = {"Marrakech": (31.6295, -7.9811), "Agadir": (30.4278, -9.5981)}

MALE_FIRST = [
    "Youssef", "Amine", "Othmane", "Anas", "Hamza", "Reda", "Imad", "Ayoub",
    "Mehdi", "Hicham", "Said", "Khalid", "Driss", "Zakaria", "Nabil",
]

FEMALE_FIRST = [
    "Fatima", "Amal", "Imane", "Salma", "Sara", "Chaima", "Meryem", "Zineb",
    "Asmae", "Soukaina", "Noura", "Samira", "Kawtar", "Yasmine", "Oumaima",
]

LAST_NAMES = [
    "Alaoui", "Bennis", "Lamrani", "Fassi", "Benani", "Chakir", "El Amrani",
    "Hafidi", "Kandil", "Mansouri", "Raji", "Sabiri", "Tazi", "Naciri",
    "Benzekri", "Daoudi", "Harrouni", "El Haiti", "Amrani", "Bouzidi",
]

SERVICE_DATA = [
    {"name": "Ménage standard",         "duration": 120, "price": 250},
    {"name": "Ménage profond",          "duration": 240, "price": 450},
    {"name": "Maintenance climatiseur", "duration":  60, "price": 300},
    {"name": "Conciergerie arrivée",    "duration":  30, "price": 150},
    {"name": "Jardinage & piscine",     "duration":  90, "price": 200},
]
# --------------------------------------------------------


fake = Faker()
fake.seed_instance(42)
random.seed(42)


def _agency_for(user):
    if hasattr(user, "profile") and getattr(user.profile, "agency", None):
        return user.profile.agency
    return Agency.objects.get_or_create(name="Default Agency", slug="default")[0]


class Command(BaseCommand):
    help = "Create 15 Moroccan employees + 25 absences + services (multi-agency)"

    def add_arguments(self, parser):
        parser.add_argument("--user", type=str, help="Super-user username", required=False)

    def handle(self, *args, **options):
        superuser = User.objects.filter(is_superuser=True).first()
        if options["user"]:
            superuser = User.objects.get(username=options["user"])

        agency = _agency_for(superuser)
        services = self.create_services(agency)
        employees = self.create_employees(agency, services)
        self.create_absences(agency, employees)
        self.stdout.write(self.style.SUCCESS(f"✅ Staff data created for agency «{agency}»"))

    # ----------------------------------------------------------
    def create_services(self, agency):
        services = []
        for svc in SERVICE_DATA:
            s, _ = Service.objects.get_or_create(
                agency=agency,
                name=svc["name"],
                defaults=dict(
                    duration=timedelta(minutes=svc["duration"]),
                    price=Decimal(svc["price"]),
                    currency="MAD",
                    down_payment=Decimal(random.randint(0, 100)),
                ),
            )
            services.append(s)
        return services

    # ----------------------------------------------------------
    def create_employees(self, agency, services):
        employees = []
        for i in range(15):
            genre = random.choice(["M", "F"])
            first = random.choice(MALE_FIRST if genre == "M" else FEMALE_FIRST)
            last = random.choice(LAST_NAMES)
            email = f"{first.lower()}.{last.lower()}@gmail.com"

            user, _ = User.objects.get_or_create(
                username=email,
                defaults=dict(first_name=first, last_name=last, email=email),
            )

            cal, _ = CustomCalendar.objects.get_or_create(
                name=f"Cal {first} {last}",
                slug=f"{first.lower()}-{last.lower()}",
            )

            emp, _ = Employee.objects.get_or_create(
                agency=agency,
                user=user,
                defaults=dict(
                    name=f"{first} {last}",
                    calendar=cal,
                    role=random.choice(["cleaner", "maintenance", "concierge"]),
                    phone_number=fake.phone_number()[:15],
                    hire_date=timezone.now().date() - timedelta(days=random.randint(30, 900)),
                    is_active=True,
                    slot_duration=30,
                    work_on_saturday=random.choice([True, False]),
                    work_on_sunday=random.choice([True, False]),
                ),
            )
            emp.services_offered.set(random.sample(services, k=random.randint(2, len(services))))
            employees.append(emp)
        return employees

    # ----------------------------------------------------------
    def create_absences(self, agency, employees):
        for _ in range(25):
            emp = random.choice(employees)
            start = timezone.now() - timedelta(days=random.randint(-60, 90))
            end = start + timedelta(days=random.randint(1, 10))

            Absence.objects.get_or_create(
                agency=agency,
                employee=emp,
                start_date=start,
                end_date=end,
                defaults=dict(
                    type_absence=random.choice(["CONG", "MALD", "NJSU"]),
                    description=fake.sentence(),
                ),
            )