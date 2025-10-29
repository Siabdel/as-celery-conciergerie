
class EmployeeMixin:
    @property
    def calendar(self):
        return getattr(self, "employee_profile", None) and self.employee_profile.calendar
