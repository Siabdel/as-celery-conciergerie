# conciergerie/managers.py
from django.db import models


 

class AgencyQuerySet(models.QuerySet):
    def for_user(self, user):
        """Employee ou Owner → filtre par agence."""
        if hasattr(user, "employee"):
            return self.filter(agency=user.employee.agency)
       
        if user.properties_owned.exists():
            # owner → filtre par l’agence de son **premier** bien
            return self.filter(agency=user.properties_owned.first().agency)
        
        return self.none()


class AgencyManager(models.Manager):
    def get_queryset(self):
        return AgencyQuerySet(self.model, using=self._db)

    def for_user(self, user):
        return self.get_queryset().for_user(user)
    
# ------------------------------------------------------------------
# Managers spécifiques (héritent d'AgencyManager)
# ------------------------------------------------------------------
class PropertyManager(AgencyManager):
    pass


class ReservationManager(AgencyManager):
    pass


class ServiceTaskManager(AgencyManager):
    pass


class PricingRuleManager(AgencyManager):
    pass