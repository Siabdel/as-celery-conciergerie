
from django.db import models
from django.utils.translation import gettext_lazy as _
from schedule.models import Calendar as BaseCalendar
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import models, IntegrityError
from django.contrib.auth import get_user_model
from django.db.models import Sum, F



## ----
class ResaStatus(models.TextChoices):
    """
    PENDING : État initial d'une réservation, en attente de confirmation.
    CONFIRMED : La réservation a été confirmée mais le séjour n'a pas encore commencé.
    IN_PROGRESS : Indique que le séjour est en cours.
    CHECKED_IN : Le client est arrivé et a pris possession du logement.
    CHECKED_OUT : Le client a quitté le logement à la fin de son séjour.
    COMPLETED : La réservation est terminée, tous les services ont été fournis.
    CANCELLED : La réservation a été annulée.
    EXPIRED : La réservation n'a pas été confirmée dans le délai imparti.
    """
    PENDING = 'PENDING', _('Pending')
    NEED_ATTENTION = 'NEED_ATTENTION', _('Need_attention')
    IN_PROGRESS = 'INPROGESS', _('In progress')
    COMPLETED = 'COMPLETED', _('Completed')
    CONFIRMED = 'CONFIRMED', _('Confirmed')
    CHECKED_IN = 'CHECKIN', _('Checked In')
    CHECKED_OUT= 'CHCKOUT', _('Checked Out')
    CANCELLED = 'CANCEL', _('Cancelled')
    EXPIRED = 'EXPIRED', _('Expired')

    
class PlatformChoices(models.TextChoices) :
    AIRBNB = 'AIRBNB', _('Airbnb')
    BOOKING = 'BOOKING', _('booking')
    DIRECT = 'DIRECT' , _('Direct Booking')
    
 
class TaskTypeService(models.TextChoices):
    CHECKED_IN = 'CHECKIN', _('Checked In')
    CHECKED_OUT= 'CHCKOUT', _('Checked Out')
    CLEANING = 'CLEAN', _('Cleanning')
    MAINTENANCE = 'MAINT', _('Maintenance')
    ERROR = 'ERROR', _('Affectation en erreur !')

#---------------
#- Base Times
#---------------
class ASBaseTimestampMixin(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, )
    update_at = models.DateTimeField(auto_created=True, default=timezone.now)
    created_by = models.ForeignKey( get_user_model(), on_delete=models.CASCADE,default=1)
    
    def save(self, *args, **kwargs):
        if not self.id:
            self.created_at = timezone.now()
        self.updated_at = timezone.now()
        return super().save(*args, **kwargs)
    class Meta:
        abstract = True

#---------------
#- Calendard
#---------------

        
class CustomCalendar(BaseCalendar):
    class Meta:
        proxy = True

    @classmethod
    def create_unique(cls, name, slug):
        if not cls.objects.filter(name=name).exists():
            return cls.objects.create(name=name, slug=slug)
        return cls.objects.get(name=name)
