from django.test import TestCase

# Create your tests here.
# staff/tests/test_api_staff.py
import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal

from core.models import Agency, CustomUser
from staff.models import Employee, Contract, Absence, PayrollEntry
from conciergerie.models import Property, Reservation, ServiceTask

pytestmark = pytest.mark.django_db


@pytest.fixture
def agency():
    return Agency.objects.create(name="HappyBee Marrakech")


@pytest.fixture
def admin_user(agency):
    user = CustomUser.objects.create_user(
        username="admin1",
        email="admin@happybee.com",
        password="pass",
        role=CustomUser.Roles.AGENCY_ADMIN,
        agency=agency,
    )
    return user


@pytest.fixture
def api_client(admin_user):
    client = APIClient()
    client.force_authenticate(admin_user)
    return client


@pytest.fixture
def employee(agency):
    u = CustomUser.objects.create_user(
        username="emp1",
        email="emp@bee.com",
        password="pass",
        role=CustomUser.Roles.EMPLOYEE,
        agency=agency,
    )
    return Employee.objects.create(user=u, agency=agency, role=Employee.Role.CLEANER)


@pytest.fixture
def contract(employee):
    return Contract.objects.create(
        employee=employee,
        contract_type="cdi",
        start_date=timezone.now().date(),
        daily_salary=Decimal("200.00"),
        active=True,
    )


def test_list_employees(api_client, employee):
    url = reverse("employee-list")
    res = api_client.get(url)
    assert res.status_code == 200
    assert any(str(employee.id) in str(res.data))


def test_create_absence(api_client, employee):
    url = reverse("absence-list")
    data = {
        "employee": employee.id,
        "start_date": "2025-10-10",
        "end_date": "2025-10-12",
        "reason": "Congés annuels",
    }
    res = api_client.post(url, data, format="json")
    assert res.status_code == status.HTTP_201_CREATED
    assert res.data["employee"] == employee.id


def test_create_service_task(api_client, employee, agency):
    prop = Property.objects.create(name="Villa Atlas", agency=agency)
    start = timezone.now()
    end = start + timezone.timedelta(hours=2)
    task = ServiceTask.objects.create(
        agency=agency,
        property=prop,
        employee=employee,
        task_type=ServiceTask.TaskType.CLEANING,
        start_time=start,
        end_time=end,
        completed=False,
    )
    assert task.task_type == ServiceTask.TaskType.CLEANING
    assert task.employee == employee


def test_mark_task_completed(api_client, employee, agency):
    prop = Property.objects.create(name="Riad Bleu", agency=agency)
    task = ServiceTask.objects.create(
        agency=agency,
        property=prop,
        employee=employee,
        task_type=ServiceTask.TaskType.MAINTENANCE,
        start_time=timezone.now(),
        end_time=timezone.now() + timezone.timedelta(hours=2),
    )
    task.completed = True
    task.save()
    assert ServiceTask.objects.filter(completed=True).count() == 1


def test_contract_visible_in_list(api_client, contract):
    url = reverse("contract-list")
    res = api_client.get(url)
    assert res.status_code == 200
    assert any(str(contract.id) in str(res.data))


def test_payroll_entry_creation(api_client, employee):
    url = reverse("payroll-list")
    data = {
        "employee": employee.id,
        "date": "2025-10-15",
        "shifts_worked": 2,
        "total_salary": "400.00",
    }
    res = api_client.post(url, data, format="json")
    assert res.status_code == 201
    assert Decimal(res.data["total_salary"]) == Decimal("400.00")

