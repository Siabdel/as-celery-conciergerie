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
    RESERVATION_STATUS = [
        ('confirmed', 'Confirmed'),
        ('pending', 'Pending'),
        ('cancelled', 'Cancelled'),
    ]
    
    PLATFORM_CHOICES = [
        ('airbnb', 'Airbnb'),
        ('booking', 'Booking.com'),
        ('direct', 'Direct Booking'),
    ]

    property = models.ForeignKey(Property, on_delete=models.CASCADE, 
                                            related_name='reservations')
    check_in = models.DateTimeField()
    check_out = models.DateTimeField()
    guest_name = models.CharField(max_length=100)
    guest_email = models.EmailField()
    
    # Nouveaux champs
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES, null=True)
    reservation_status = models.CharField(max_length=20, 
                                          choices=RESERVATION_STATUS, default='pending')
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

    def save(self, *args, **kwargs):
        if self.check_in > self.check_out :
            raise ValidationError("choisir une date d'entree inferieur a la date de check_out !!")
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
    class TaskStatus(models.TextChoices):
        PENDING = 'PEND', _('Pending')
        IN_PROGRESS = 'PROG', _('In progress')
        COMPLETED = 'COMP', _('Completed')
    
    class TypeService(models.TextChoices):
        CHECK_IN = 'CKIN', _('Check_in')
        CHECK_OUT = 'CKOU', _('Check_out')
        CLEANING = 'CLEAN', _('Cleanning')
        MAINTENANCE = 'MAINT', _('Maintenance')
        ERROR = 'ERROR', _('Affectation en erreur !')
    
    employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, related_name='%(class)s_tasks')
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='%(class)s_tasks')
    reservation = models.ForeignKey(Reservation, on_delete=models.SET_NULL, null=True, related_name='%(class)s_tasks')
    description = models.TextField()
    start_date  = models.DateTimeField()
    end_date    = models.DateTimeField()
    status = models.CharField(max_length=20, choices=TaskStatus.choices, default=TaskStatus.PENDING)
    type_service = models.CharField(max_length=20, choices=TypeService.choices, default=TypeService.CHECK_IN)
    completed = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ("start_date", "end_date", "employee", "property", )
        ordering = ['property', 'end_date',]

    def __str__(self):
        return f"Task for {self.property} - {self.end_date}"

    def mark_as_completed(self):
        self.completed = True
        self.save()
    
    def mark_as_completed(self):
        self.completed = True
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
