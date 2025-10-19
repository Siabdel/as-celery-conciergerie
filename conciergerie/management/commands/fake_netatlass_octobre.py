
# conciergerie/management/commands/fake_netatlass_octobre.py
import random, os
from decimal import Decimal
from datetime import datetime, timedelta, time

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from conciergerie.models import (
    Property, Reservation, PricingRule,
    ServiceTask, TaskTypeService, Incident, AdditionalExpense,
    CheckoutInventory, CheckoutPhoto,
)
from staff.models import Employee, Service
from core.models import PlatformChoices, ReservationStatus, Agency
from faker import Faker
fake = Faker()

User = get_user_model()

# ---------- Moroccan data ----------
MARR_LAT, MARR_LON = 31.6295, -7.9811
FIRST_M = ["Youssef", "Amine", "Othmane", "Anas", "Hamza"]
FIRST_F = ["Fatima", "Amal", "Imane", "Salma", "Chaima"]
LAST = ["Alaoui", "Bennis", "Lamrani", "Fassi", "Benani"]

# ---------- pictures already shipped in static/img ----------
POOL_PHOTOS = [
    "avatar_residence.jpg",
    "Happy_Bee_01.jpg",
    "Happy_Bee_02.jpg",
    "illustration_conciergerie.jpg",
    "illustration_conciergerie_Marrakech.jpg",
    "illustration_conciergerie_Nadiato2.jpg",
]


# ------------------------------------------------------------------
class Command(BaseCommand):
    help = "Crée 2 proprios, 2 apparts Marrakech, ~15 résas Oct-2025 sans générer d’image (photos static/img)"

    # ----------------------------------------------------------
    def handle(self, *args, **options):
        try:
            abdel = User.objects.get(username="abdel")
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR("❌  Créez d'abord un user username=abdel"))
            return

        agency, _ = Agency.objects.get_or_create(
            name="Netatlass Conciergerie",
            defaults=dict(
                created_by=abdel,
                code = "A001",
                phone="+212600000000",
                email="contact@netatlass.ma",
                address="Rue Ibn Toumert, Marrakech",
            ),
        )

        employees = self.create_employees(agency)
        owners = self.create_owners()
        apparts = self.create_apparts(owners, agency)
        self.create_pricing_rules(apparts)
        self.create_reservations(apparts, agency, employees)
        self.stdout.write(self.style.SUCCESS("✅  Fake Netatlass Octobre 2025 créées (photos static/img) !"))

    # ----------------------------------------------------------
    def create_owners(self):
        owners = []
        for i in range(2):
            first = random.choice(FIRST_M + FIRST_F)
            last = random.choice(LAST)
            email = f"{first.lower()}.{last.lower()}@gmail.com"
            u, _ = User.objects.get_or_create(
                username=email,
                defaults=dict(first_name=first, last_name=last, email=email),
            )
            owners.append(u)
        return owners

    # ----------------------------------------------------------
    def create_apparts(self, owners, agency):
        apparts = []
        for i in range(2):
            apt, _ = Property.objects.get_or_create(
                agency=agency,
                name=f"Appart Marrakech Gueliz {i+1}",
                defaults=dict(
                    owner=owners[i],
                    type="apartment",
                    address=f"{fake.building_number()} Rue Ibn Toumert, Gueliz, Marrakech",
                    latitude=MARR_LAT + random.uniform(-0.01, 0.01),
                    longitude=MARR_LON + random.uniform(-0.01, 0.01),
                    price_per_night=Decimal(random.randint(450, 850)),
                    capacity=random.randint(2, 5),
                    is_active=True,
                ),
            )
            apparts.append(apt)
        return apparts

    # ----------------------------------------------------------
    def create_pricing_rules(self, apparts):
        for apt in apparts:
            PricingRule.objects.get_or_create(
                agency=apt.agency,
                property=apt,
                start_date=timezone.now().date(),
                end_date=timezone.now().date() + timedelta(days=60),
                defaults=dict(
                    price_per_night=apt.price_per_night + Decimal(random.randint(-50, 100)),
                    is_active=True,
                    priority=1,
                    min_nights=1,
                ),
            )

    # ----------------------------------------------------------
    def create_reservations(self, apparts, agency, employees):
        created = 0
        while created < 15:
            apt = random.choice(apparts)
            check_in = timezone.make_aware(datetime(2025, 10, random.randint(1, 28), 14, 0))
            check_out = check_in + timedelta(days=random.randint(2, 5))

            total = apt.get_price_for_date(check_in.date()) * (check_out - check_in).days

            try:
                resa = Reservation.objects.create(
                    agency=agency,
                    property=apt,
                    check_in=check_in,
                    check_out=check_out,
                    guest_name=f"{random.choice(FIRST_M + FIRST_F)} {random.choice(LAST)}",
                    guest_email=fake.email(),
                    platform=random.choice([PlatformChoices.AIRBNB, PlatformChoices.BOOKING]),
                    number_of_guests=random.randint(1, 4),
                    total_price=total,
                    cleaning_fee=Decimal(random.randint(100, 300)),
                    service_fee=Decimal(random.randint(50, 150)),
                    reservation_status=ReservationStatus.CONFIRMED,
                    nights=(check_out - check_in).days,
                    currency="MAD",
                )
                self.create_side_objects(resa, employees)
                created += 1
            except IntegrityError:
                continue  # duplicate check-in

    # ----------------------------------------------------------
    def create_side_objects(self, resa, employees):
        agency = resa.agency
        employee = random.choice(employees) if employees else None

        # ----- ServiceTask -----
        ServiceTask.objects.get_or_create(
            agency=agency,
            property=resa.property,
            reservation=resa,
            start_date=resa.check_in - timedelta(hours=1),
            end_date=resa.check_in + timedelta(hours=1),
            defaults=dict(
                type_service=TaskTypeService.CHECKED_IN,
                description="Remise des clés & check-in",
                employee=employee,
            ),
        )

        # ----- Incident (40 % chance) -----
        if random.random() < 0.4:
            Incident.objects.create(
                agency=agency,
                property=resa.property,
                title="Petit problème électrique",
                reported_by=employee,
                type="PANNE",
                description="Prise salon hors-service",
            )

        # ----- AdditionalExpense -----
        AdditionalExpense.objects.create(
            agency=agency,
            property=resa.property,
            expense_type="cleaning",
            amount=Decimal(random.randint(80, 250)),
            description="Ménage fin de séjour",
            date_incurred=resa.check_out.date(),
            incurred_by=employee,
        )

        # ----- CheckoutInventory -----
        inv, _ = CheckoutInventory.objects.get_or_create(
            agency=agency,
            reservation=resa,
            defaults=dict(
                employee=employee,
                cleanliness_rating=random.randint(3, 5),
                is_completed=True,
            ),
        )
        # ----- CheckoutPhoto (no physical file, only path) -----
        CheckoutPhoto.objects.create(
            agency=agency,
            image="",  # ← empty file field
            description="Salon après départ",
        )

    # ----------------------------------------------------------
    def create_employees(self, agency):
        """Create 3 Netatlass employees."""
        services = self.create_services()
        employees = []
        for i in range(3):
            first = random.choice(FIRST_M + FIRST_F)
            last = random.choice(LAST)
            email = f"netatlass.{first.lower()}.{last.lower()}@gmail.com"
            user, _ = User.objects.get_or_create(
                username=email,
                defaults=dict(first_name=first, last_name=last, email=email),
            )

            from core.models import CustomCalendar
            cal, _ = CustomCalendar.objects.get_or_create(
                name=f"Calendrier {first} {last}",
                slug=f"{first.lower()}-{last.lower()}",
            )

            emp, _ = Employee.objects.get_or_create(
                user=user,
                defaults=dict(
                    agency=agency,
                    role=random.choice(["cleaner", "maintenance", "concierge"]),
                    phone_number=fake.phone_number()[:15],
                    hire_date=timezone.now().date() - timedelta(days=random.randint(30, 300)),
                    is_active=True,
                    slot_duration=30,
                    calendar=cal,
                ),
            )
            emp.services_offered.set(services)
            employees.append(emp)
        return employees

    # ----------------------------------------------------------
    def create_services(self):
        """Minimal services if DB empty."""
        from datetime import timedelta
        services = []
        for name, minutes, price in [
            ("Ménage standard", 120, 250),
            ("Maintenance clim", 60, 300),
            ("Conciergerie arrivée", 30, 150),
        ]:
            s, _ = Service.objects.get_or_create(
                agency=Agency.objects.first(),  # any agency – we only need the list
                name=name,
                defaults=dict(
                    duration=timedelta(minutes=minutes),
                    price=Decimal(price),
                    currency="MAD",
                ),
            )
            services.append(s)
        return services