from rest_framework.test import APITestCase
from django.urls import reverse
from core.models import CustomUser, Agency
from staff.models import Employee

class AgencyScopedAPITest(APITestCase):
    def setUp(self):
        self.agency = Agency.objects.create(name="Happy Bee", slug="happy-bee", code="bee01")
        self.admin = CustomUser.objects.create_user(
            username="admin",
            password="pass",
            agency=self.agency,
            role=CustomUser.Roles.AGENCY_ADMIN,
        )
        self.client.force_authenticate(self.admin)

    def test_employee_creation_scopes_agency(self):
        url = reverse("employee-list")
        response = self.client.post(url, {
            "user": None, "role": "concierge", "is_active": True
        })
        self.assertEqual(response.status_code, 201)
        emp = Employee.objects.last()
        self.assertEqual(emp.agency, self.admin.agency)

