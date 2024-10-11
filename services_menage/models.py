from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from schedule.models import Event, Calendar
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models, IntegrityError
from schedule.models import Calendar as BaseCalendar

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


class Calendar(BaseCalendar):
    class Meta:
        proxy = True

    @classmethod
    def create_unique(cls, name, slug):
        if not cls.objects.filter(name=name).exists():
            return cls.objects.create(name=name, slug=slug)
        return cls.objects.get(name=name)

class Property(models.Model):
    PROPERTY_TYPES = [
        ('apartment', 'Apartment'),
        ('house', 'House'),
        ('villa', 'Villa'),
    ]
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=PROPERTY_TYPES)
    address = models.TextField()
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='properties')
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2, default=0) # Ajoutez cette ligne

    def __str__(self):
        return f"{self.name} ({self.type})"
        
    def get_active_listings(self):
        return self.listings.filter(is_active=True)

    def get_upcoming_reservations(self):
        return self.reservations.filter(check_in__gte=timezone.now().date())

class Reservation(models.Model):
    
    reservation_status = models.CharField(max_length=20, 
                                          choices=ResaStatus.choices, 
                                          default=ResaStatus.PENDING)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='reservations')
    check_in = models.DateTimeField()
    check_out = models.DateTimeField()
    guest_name = models.CharField(max_length=100)
    guest_email = models.EmailField()
    
    # Nouveaux champs
    platform = models.CharField(max_length=20, 
                                choices=PlatformChoices.choices, 
                                default=PlatformChoices.AIRBNB, null=True)
    number_of_guests = models.PositiveIntegerField(validators=[MinValueValidator(1)], 
                                                   default=1)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    cleaning_fee = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    service_fee = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    guest_phone = models.CharField(max_length=20, blank=True)
    special_requests = models.TextField(blank=True)
    is_business_trip = models.BooleanField(default=False)
    guest_rating = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], null=True, blank=True)
    cancellation_policy = models.CharField(max_length=100, blank=True)
    booking_date = models.DateTimeField(auto_now_add=True)
    
    class Meta :
        ordering = ("property", "check_in", )
        unique_together = ("property", "check_in", )
    
    def get_duration(self):
        return (self.check_out - self.check_in).days + 1

    def calculate_total_price(self):
        duration = self.get_duration()
        return (self.property.price_per_night * duration) + self.cleaning_fee + self.service_fee

    def clean(self):
        """
        Cette méthode vérifie la validité du statut de la réservation par rapport aux dates importantes.
        """
        aujourdhui = timezone.now()


        if self.check_in > self.check_out :
            raise ValidationError("choisir une date d'entree inferieur a la date de check_out !!")
        
        # Vérification des statuts incohérents avec la date actuelle et les dates de check-in/check-out
        if self.check_out and aujourdhui > self.check_out:
            if self.reservation_status == ResaStatus.PENDING:
                raise ValidationError("Le statut 'PENDING' est impossible si la date actuelle est après le check-out.")
            if self.reservation_status == ResaStatus.CONFIRMED:
                raise ValidationError("Le statut 'CONFIRMED' est impossible après la date de check-out.")
            if self.reservation_status == ResaStatus.CHECKED_IN:
                raise ValidationError("Le statut 'CHECKED_IN' est impossible après la date de check-out.")

        if self.check_in and aujourdhui > self.check_in and self.reservation_status == ResaStatus.PENDING:
            raise ValidationError("Le statut 'PENDING' est impossible si la date actuelle est après la date de check-in.")
        
        if self.reservation_status == ResaStatus.CHECKED_OUT and aujourdhui < self.check_out:
            raise ValidationError("Le statut 'CHECKED_OUT' ne peut pas être défini avant le check-out.")

        if self.reservation_status == ResaStatus.EXPIRED and aujourdhui <= self.check_out:
            raise ValidationError("Le statut 'EXPIRED' ne peut être défini que si la date de check-out est passée.")

    def save(self, *args, **kwargs):
        """
        Surcharge de la méthode `save()` pour inclure la validation avant la sauvegarde.
        """
        # Appel de la méthode clean() pour valider les règles métier
        ##self.clean()
        #raise ValidationError("quelle est le status ", self.reservation_status)
        super().save(*args, **kwargs)
##
        if not self.total_price:
            self.total_price = self.calculate_total_price()
        try :
            super().save(*args, **kwargs)
        except IntegrityError as err:
            # Au lieu de cela, levez une exception personnalisée
            raise ValidationError("Une réservation existe déjà pour cette \
                propriété à cette date. Veuillez choisir une autre date ou \
                    une autre propriété.")

    def __str__(self):
        return f"Reservation for {self.property} from {self.check_in} to {self.check_out}"



class Employee(models.Model):
    ROLE_CHOICES = [
        ('cleaner', 'Cleaner'),
        ('maintenance', 'Maintenance'),
        ('concierge', 'Concierge'),
        ('manager', 'Manager'),
    ]
    name = models.CharField(max_length=100)
    calendar = models.ForeignKey(Calendar, on_delete=models.CASCADE)
    user = models.OneToOneField(User, null=True, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='cleaner')
    phone_number = models.CharField(max_length=15, null=True)
    hire_date = models.DateField() # date d'embauche
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} - {self.get_role_display()}"

class ServiceTask(models.Model):
   
    employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, 
                                 null=True, related_name='%(class)s_tasks')
    property = models.ForeignKey(Property, on_delete=models.CASCADE, 
                                 related_name='%(class)s_tasks')
    reservation = models.ForeignKey(Reservation, null=True, on_delete=models.CASCADE,
                                    related_name='%(class)s_tasks')
    description = models.TextField()
    start_date  = models.DateTimeField()
    end_date    = models.DateTimeField()
    status = models.CharField(max_length=20, choices=ResaStatus.choices, 
                              default=ResaStatus.PENDING)
    type_service = models.CharField(max_length=20, choices=TaskTypeService.choices, 
                                    default=TaskTypeService.CHECKED_IN)
    completed = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ("start_date", "end_date", "employee", "property", )
        ordering = ['property', 'end_date',]

    def __str__(self):
        return f"Task for {self.property} - {self.end_date}"

    def mark_as_completed(self):
        self.completed = True
        self.status = self.TaskStatus.COMPLETED
        self.save()

        
class Absence(models.Model):
    class TypeAbsence(models.TextChoices):
        CONGES = 'CONG', _('En conges')
        MALADIE = 'MALD', _('En maladie')
        INCONNU = 'NJSU', _('Non justifier')
    
    type_absence = models.CharField(max_length=200, 
                                    choices=TypeAbsence.choices,
                                    default=TypeAbsence.INCONNU)

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    
    def __str__(self) -> str:
        return f"Absence for {self.employee} - {self.start_date}"
