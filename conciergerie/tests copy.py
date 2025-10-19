from django.test import TestCase

# Create your tests here.

# conciergerie/tests.py
import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from .models import Property, Reservation
from datetime import date, timedelta

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def owner():
    return User.objects.create_user(
        username="owner", password="test", email="o@test.com"
    )


@pytest.fixture
def property_obj(owner):
    return Property.objects.create(
        name="Villa Bleue", type="villa", owner=owner, price_per_night=100
    )


@pytest.mark.django_db
def test_create_reservation(api_client, owner, property_obj):
    api_client.force_authenticate(user=owner)
    url = reverse("reservation-list")
    start = date.today() + timedelta(days=10)
    end = date.today() + timedelta(days=13)
    payload = {
        "property": property_obj.id,
        "check_in": start,
        "check_out": end,
        "guest_name": "Alice",
        "guest_email": "alice@test.com",
        "number_of_guests": 2,
    }
    resp = api_client.post(url, payload, format="json")
    assert resp.status_code == 201
    assert resp.data["duration"] == 3


@pytest.mark.django_db
def test_property_revenue(api_client, owner, property_obj):
    api_client.force_authenticate(user=owner)
    Reservation.objects.create(
        property=property_obj,
        check_in=date.today(),
        check_out=date.today() + timedelta(days=2),
        guest_name="B",
        guest_email="b@test.com",
        total_price=300,
        reservation_status="CONFIRMED",
    )
    url = reverse("property-revenue", kwargs={"pk": property_obj.id})
    resp = api_client.get(url, {"year": date.today().year})
    assert resp.status_code == 200
    # current month should have 300
    month_name = resp.data[date.today().month - 1]["month"]
    assert resp.data[date.today().month - 1]["revenue"] == 300

    
    