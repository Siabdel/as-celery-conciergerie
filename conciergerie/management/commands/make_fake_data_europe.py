# your_app/management/commands/make_fake_data.py
import random
from datetime import timedelta, date, datetime, time
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from faker import Faker
# dans la méthode create_pricing_rules
from dateutil.relativedelta import relativedelta   # <-- ajout
from core.models import ReservationStatus, PlatformChoices
from services_menage.models import Property, Reservation, PricingRule, ServiceTask, TaskTypeService
# from services_menage.models import Incident, AdditionalExpense, CheckoutInventory, CheckoutPhoto

User = get_user_model()
fake = Faker()
Faker.seed(42)          # reproducible
random.seed(42)

# settings
N_OWNERS   = 15
N_APT      = 10
N_HOUSE    = 5
N_BOOKINGS = 100        # final count ≈ N_BOOKINGS


def _random_date(start, end):
    """Return a random date between two date objects."""
    delta = end - start
    return start + timedelta(days=random.randint(0, delta.days))


def _random_dt(start, end):
    """Return a random datetime between two datetime objects."""
    delta = end - start
    return start + timedelta(seconds=random.randint(0, int(delta.total_seconds())))


class Command(BaseCommand):
    help = "Generate fake data for the concierge project (owners, properties, reservations, …)"

    def handle(self, *args, **options):
        owners = self.create_owners()
        props  = self.create_properties(owners)
        self.create_reservations(props)
        self.stdout.write(self.style.SUCCESS("✅ Fake data created successfully!"))

    # ------------------------------------------------------------------
    def create_owners(self):
        self.stdout.write("👥 Creating owners …")
        owners = []
        for i in range(N_OWNERS):
            first = fake.first_name()
            last  = fake.last_name()
            email = f"{first.lower()}.{last.lower()}@example.com"
            user, _ = User.objects.get_or_create(
                username=email,
                defaults=dict(
                    first_name=first,
                    last_name=last,
                    email=email,
                    password="pbkdf2_sha256$…",  # unusable password
                ),
            )
            owners.append(user)
        return owners

    # ------------------------------------------------------------------
    def create_properties(self, owners):
        self.stdout.write("🏘  Creating properties …")
        props = []

        # 10 apartments
        for i in range(N_APT):
            p = self._property(
                owner=random.choice(owners),
                type="apartment",
                name=f"Lovely Apt {i+1}",
            )
            props.append(p)

        # 5 houses
        for i in range(N_HOUSE):
            p = self._property(
                owner=random.choice(owners),
                type="house",
                name=f"Cosy House {i+1}",
            )
            props.append(p)

        # create 1-3 pricing rules per property
        for prop in props:
            self.create_pricing_rules(prop)
        return props

    # ------------------------------------------------------------------
    def _property(self, owner, type, name):
        lat, lng = fake.local_latlng(country_code="FR")[:2]
        prop, _ = Property.objects.get_or_create(
            name=name,
            defaults=dict(
                owner=owner,
                type=type,
                address=fake.address().replace("\n", ", "),
                latitude=float(lat),
                longitude=float(lng),
                price_per_night=Decimal(random.randint(60, 350)),
            ),
        )
        return prop

    # ------------------------------------------------------------------
    def create_pricing_rules(self, prop):
        # dans la méthode create_pricing_rules

        base = prop.price_per_night
        today = timezone.now().date()
        for _ in range(random.randint(1, 3)):
            start = _random_date(today, today.replace(year=today.year + 1))
            end   = _random_date(start, start + relativedelta(months=2))  # <-- fix
            price = base + Decimal(random.randint(-20, 50))
        
            PricingRule.objects.get_or_create(
                property=prop,
                start_date=start,
                end_date=end,
                defaults=dict(
                    price_per_night=price,
                    is_active=True,
                    priority=random.randint(0, 5),
                    min_nights=random.randint(1, 3),
                ),
            )

    # ------------------------------------------------------------------
    def create_reservations(self, props):
        self.stdout.write("📅 Creating reservations …")
        today = timezone.now().date()
        for _ in range(N_BOOKINGS):
            prop   = random.choice(props)
            # random check-in within next 12 months
            check_in_date = _random_date(today, today.replace(year=today.year + 1))
            duration      = random.randint(1, 14)
            check_out_date = check_in_date + timedelta(days=duration)

            # coherent status
            now_dt = timezone.now()
            check_in_dt  = timezone.make_aware(datetime.combine(check_in_date, time(14, 0)))
            check_out_dt = timezone.make_aware(datetime.combine(check_out_date, time(12, 0)))

            if check_out_dt < now_dt:
                status = random.choice([ReservationStatus.COMPLETED, ReservationStatus.CHECKED_OUT])
            elif check_in_dt <= now_dt <= check_out_dt:
                status = random.choice([ReservationStatus.CHECKED_IN, ReservationStatus.IN_PROGRESS])
            elif check_in_dt <= now_dt + timedelta(days=7):
                status = random.choice([ReservationStatus.CONFIRMED, ReservationStatus.NEEDS_ATTENTION])
            else:
                status = ReservationStatus.PENDING

            total = prop.get_price_for_date(check_in_date) * duration

            reservation, created = Reservation.objects.get_or_create(
                property=prop,
                check_in=check_in_dt,
                defaults=dict(
                    check_out=check_out_dt,
                    guest_name=fake.name(),
                    guest_email=fake.email(),
                    platform=random.choice(PlatformChoices.choices)[0],
                    number_of_guests=random.randint(1, 6),
                    total_price=total,
                    cleaning_fee=Decimal(random.randint(20, 80)),
                    service_fee=Decimal(random.randint(5, 30)),
                    reservation_status=status,
                ),
            )

            # optional related objects
            # self.create_tasks(reservation)
            # self.create_incidents(reservation.property)
            # self.create_expenses(reservation.property)
            # self.create_checkout_inventory(reservation)

    # ------------------------------------------------------------------
    # Below: helpers for optional related objects (uncomment if desired)
    # ------------------------------------------------------------------
    def create_tasks(self, reservation):
        ServiceTask.objects.get_or_create(
            property=reservation.property,
            reservation=reservation,
            start_date=reservation.check_in - timedelta(hours=2),
            end_date=reservation.check_in,
            type_service=TaskTypeService.CHECKED_IN,
            defaults=dict(description="Check-in task", employee=None),
        )
        ServiceTask.objects.get_or_create(
            property=reservation.property,
            reservation=reservation,
            start_date=reservation.check_out,
            end_date=reservation.check_out + timedelta(hours=2),
            type_service=TaskTypeService.CHECKED_OUT,
            defaults=dict(description="Check-out + cleaning", employee=None),
        )

    def create_incidents(self, prop):
        pass  # implement if needed

    def create_expenses(self, prop):
        pass  # implement if needed

    def create_checkout_inventory(self, reservation):
        pass  # implement if needed