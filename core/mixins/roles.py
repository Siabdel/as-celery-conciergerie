
# core/mixins/roles.py
from core.models import CustomUser

class AgencyAdminMixin:
    """Comportements propres à un administrateur d’agence."""

    @property
    def managed_agency(self):
        return self.agency

    def get_all_employees(self):
        from staff.models import Employee
        return Employee.objects.filter(agency=self.agency)

    def get_all_properties(self):
        from conciergerie.models import Property
        return Property.objects.filter(agency=self.agency)


class EmployeeMixin:
    """Comportements propres à un employé (concierge, technicien, etc.)."""

    @property
    def calendar(self):
        return getattr(self, "employee_profile", None) and self.employee_profile.calendar

    def get_assigned_tasks(self):
        from conciergerie.models import ServiceTask
        if hasattr(self, "employee_profile"):
            return ServiceTask.objects.filter(employee=self.employee_profile)
        return ServiceTask.objects.none()


class OwnerMixin:
    """Comportements propres à un propriétaire de biens."""

    def get_owned_properties(self):
        from conciergerie.models import Property
        return Property.objects.filter(owner=self)

    def get_reservations(self):
        from conciergerie.models import Reservation
        return Reservation.objects.filter(property__owner=self)
