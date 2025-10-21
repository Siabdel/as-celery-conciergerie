# staff/api/views.py
from conciergerie.models import ServiceTask
from conciergerie.api.serializers import ServiceTaskSerializer

class StaffTaskViewSet(AgencyScopedViewSetMixin):
    """
    Vue RH pour visualiser les tâches opérationnelles assignées aux employés.
    """
    queryset = ServiceTask.objects.select_related("employee", "property", "reservation")
    serializer_class = ServiceTaskSerializer
    permission_classes = [IsEmployeeOrAgencyAdmin]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.role == CustomUser.Roles.EMPLOYEE:
            return qs.filter(employee__user=user)
        return qs
