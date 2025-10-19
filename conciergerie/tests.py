# tests.py
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.management import call_command
from datetime import timedelta

from core.models import Agency, CustomUser
from staff.models import Employee, Service
from conciergerie.models import Property, Reservation
from staff.models import CustomCalendar

User = get_user_model()

class InitialDataTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        """
        Crée une agence 'Happy Bee' Marrakech avec:
         - 2 agency admins
         - 10 owners
         - 5 employees
         - 10 properties (apparts) rattachés à owners (répartis)
         - (optionnel) quelques réservations
        """

        # 1) Create agency
        cls.agency = Agency.objects.create(
            name="Happy Bee",
            code="happy-bee-marrakech",
            phone="+212600000000",
            email="contact@happybee.example",
            slug="happy-bee-marrakech",
            is_active=True
        )

        # 2) Create 2 agency admins
        cls.admins = []
        for i in range(2):
            u = User.objects.create_user(
                username=f"agency_admin_{i+1}",
                email=f"admin{i+1}@happybee.test",
                password="testpass123",
                role=CustomUser.Roles.AGENCY_ADMIN,
                agency=cls.agency,
                is_staff=True,
            )
            cls.admins.append(u)

        # 3) Create 10 owners
        cls.owners = []
        for i in range(10):
            u = User.objects.create_user(
                username=f"owner_{i+1}",
                email=f"owner{i+1}@happybee.test",
                password="ownerpass",
                role=CustomUser.Roles.OWNER,
                agency=cls.agency,
            )
            cls.owners.append(u)

        # 4) Create 5 employees and attach them to users
        cls.employees = []
        for i in range(5):
            u = User.objects.create_user(
                username=f"employee_user_{i+1}",
                email=f"employee{i+1}@happybee.test",
                password="emppass",
                role=CustomUser.Roles.EMPLOYEE,
                agency=cls.agency,
            )
            emp = Employee.objects.create(
                user=u,
                role='concierge',
                agency=cls.agency,
                phone_number=f"+2126000000{10+i}",
                hire_date=timezone.now().date()
            )
            # create calendar explicitly (avoid depending on signals)
            CustomCalendar.objects.create(
                agency=cls.agency,
                employee=emp,
                name=f"Calendar {emp.get_staff_member_name()}",
            )
            cls.employees.append(emp)

        # 5) Create 10 properties (apartments) and attach to owners in round-robin
        cls.properties = []
        for i in range(10):
            owner = cls.owners[i % len(cls.owners)]
            prop = Property.objects.create(
                agency=cls.agency,
                name=f"Happy Apt {i+1}",
                type='apartment',
                owner=owner,
                price_per_night=100 + i * 5,
                address=f"Quartier {i+1}, Marrakech",
                latitude=31.6295 + i * 0.001,
                longitude=-7.9811 + i * 0.001,
                capacity=2 + (i % 3),
                is_active=True
            )
            cls.properties.append(prop)

        # 6) Create a handful of reservations for first 3 properties
        cls.reservations = []
        now = timezone.now()
        for idx, prop in enumerate(cls.properties[:3]):
            for j in range(2):  # two reservations each
                check_in = now + timedelta(days=7 + idx * 3 + j*2)
                check_out = check_in + timedelta(days=2)
                reservation = Reservation.objects.create(
                    agency=cls.agency,
                    property=prop,
                    reservation_status='CONFIRMED',
                    check_in=check_in,
                    check_out=check_out,
                    guest_name=f"Guest {idx}-{j}",
                    guest_email=f"guest{idx}{j}@example.test",
                    number_of_guests=2,
                    total_price=prop.price_per_night * ((check_out - check_in).days),
                    cleaning_fee=10,
                    service_fee=5,
                )
                cls.reservations.append(reservation)

    def test_counts(self):
        # basic counts
        self.assertEqual(Agency.objects.count(), 1)
        self.assertEqual(User.objects.filter(role=CustomUser.Roles.AGENCY_ADMIN).count(), 2)
        self.assertEqual(User.objects.filter(role=CustomUser.Roles.OWNER).count(), 10)
        self.assertEqual(Employee.objects.filter(agency=self.agency).count(), 5)
        self.assertEqual(Property.objects.filter(agency=self.agency).count(), 10)
        self.assertTrue(CustomCalendar.objects.filter(agency=self.agency).count() >= 5)

    def test_properties_have_correct_owners_and_agency(self):
        for p in self.properties:
            self.assertEqual(p.agency, self.agency)
            self.assertEqual(p.owner.agency, self.agency)

    def test_employees_have_calendar(self):
        for emp in self.employees:
            # verify calendar exists and belongs to same agency
            self.assertTrue(hasattr(emp, "employee_calendar"))
            self.assertEqual(emp.employee_calendar.agency, self.agency)

    def test_reservations_linked(self):
        for r in self.reservations:
            self.assertEqual(r.agency, self.agency)
            self.assertEqual(r.property.agency, self.agency)
            self.assertTrue(r.get_duration() > 0)
