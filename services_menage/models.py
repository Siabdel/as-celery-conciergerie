from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.urls import reverse, resolve
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models, IntegrityError
from django.contrib.auth import get_user_model
from django.db.models import Sum, F
from phonenumber_field.modelfields import PhoneNumberField
from staff.models import Employee
from core.models import ASBaseTimestampMixin
from django.conf import settings    
from core.models import ResaStatus, TaskTypeService, PlatformChoices, BaseImage
from core import models as cr_models 
from django.utils.text import slugify
from staff.models import Employee


class PropertyImage(cr_models.BaseImage):
    property = models.ForeignKey('Property', related_name="images", on_delete=models.CASCADE)

    def get_absolute_url(self):
        if self.slug:
            return reverse('image-detail', kwargs={'slug': self.slug})
        else:
            # Si le slug n'est pas défini, on le crée à partir du titre
            self.slug = slugify(self.title)
            self.save()
            return reverse('image-detail', kwargs={'slug': self.slug}) 

## -------------------------
##-
## -------------------------
class Property(ASBaseTimestampMixin):
    PROPERTY_TYPES = [
        ('apartment', 'Apartment'),
        ('house', 'House'),
        ('villa', 'Villa'),
    ]
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=PROPERTY_TYPES)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='properties')
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2, default=0) # Ajoutez cette ligne
    address = models.CharField(max_length=255)
    latitude = models.FloatField()
    longitude = models.FloatField()

    class Meta:
        verbose_name = 'Property'
        verbose_name_plural = 'Properties'

    def __str__(self):
        return f"{self.name} ({self.type})"
    
    
    def get_price_for_date(self, date=None):
        if date is None:
            date = timezone.now().date()
        
        # Chercher une règle de prix active pour la date donnée
        rule = self.pricing_rules.filter(
            start_date__lte=date,
            end_date__gte=date,
            is_active=True
        ).order_by('-priority').first()

        # Si une règle est trouvée, retourner son prix, sinon retourner le prix de base
        return rule.price_per_night if rule else self.price_per_night

    def get_current_price(self):
        return self.get_price_for_date()

        
    def get_active_listings(self):
        return self.listings.filter(is_active=True)

    def get_upcoming_reservations(self):
        return self.reservations.filter(check_in__gte=timezone.now().date())
    
    def get_images(self):
        return self.images.all()

    def get_absolute_url(self):
        return reverse("shop:product_detail", kwargs={'pk': self.pk})
    
    def get_edit_url(self):
        return reverse("shop:product_edit", kwargs={'pk': self.pk})

    def get_delete_url(self):
        return reverse("shop:product_delete", kwargs={'pk': self.pk})
    

class PricingRule(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='pricing_rules')
    start_date = models.DateField()
    end_date = models.DateField()
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Ajouts suggérés
    is_active = models.BooleanField(default=True)
    priority = models.IntegerField(default=0)
    min_nights = models.PositiveIntegerField(default=1)
    max_nights = models.PositiveIntegerField(null=True, blank=True)
    
    class Meta:
        ordering = ['-start_date', 'priority']

    def __str__(self):
        return f"{self.property} - {self.start_date} to {self.end_date}: {self.price_per_night}"

    def clean(self):
        if self.start_date > self.end_date:
            raise ValidationError("La date de début doit être antérieure à la date de fin.")
        # Vérifier le chevauchement avec d'autres règles de tarification
        overlapping_rules = PricingRule.objects.filter(
            property=self.property,
            start_date__lte=self.end_date,
            end_date__gte=self.start_date
        ).exclude(pk=self.pk)
        if overlapping_rules.exists():
            raise ValidationError("Cette règle de tarification chevauche une règle existante.")

    def save(self, *args, **kwargs):
        if self.start_date > self.end_date:
            raise ValueError("End date must be after start date")
        super().save(*args, **kwargs)

    def is_active_price(self):
        today = timezone.now().date()
        return self.start_date <= today <= self.end_date



  
class Reservation(ASBaseTimestampMixin):
    
    reservation_status = models.CharField(max_length=20, 
                                          choices=ResaStatus.choices, 
                                          default=ResaStatus.PENDING)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='reservations')

    check_in = models.DateTimeField(default=timezone.now().replace(hour=14, minute=0, second=0, microsecond=0))
    check_out = models.DateTimeField(default=timezone.now().replace(hour=12, minute=0, second=0, microsecond=0))
    
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

        if self.reservation_status == ResaStatus.COMPLETED and aujourdhui <= self.check_out:
            raise ValidationError("Le statut 'COMPLETED' ne peut être défini que si la date de check-out n'est pas passée.")

    def save(self, *args, **kwargs):
        if not self.total_price:
            self.total_price = self.calculate_total_price()
        super().save(*args, **kwargs)   # laisse l'IntegrityError remonter
    
   

    def __str__(self):
        return f"Reservation for {self.property} from {self.check_in} to {self.check_out}"

class ServiceTask(ASBaseTimestampMixin):
   
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
        unique_together = ("property", "start_date", "type_service")
        ordering = ['property', 'end_date',]

    def __str__(self):
        return f"Task for {self.property} - {self.end_date}"

    def mark_as_completed(self):
        self.completed = True
        self.status = self.TaskStatus.COMPLETED
        self.save()

 

 
#---------------------------------------
#-Etat des lieux du bien               -
#---------------------------------------
class CheckoutInventory(models.Model):
    reservation = models.OneToOneField(Reservation, on_delete=models.CASCADE, related_name='checkout_inventory')
    employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, related_name='checkout_inventories')
    date_performed = models.DateTimeField(auto_now_add=True)
    
    cleanliness_rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    damage_description = models.TextField(blank=True)
    missing_items = models.TextField(blank=True)
    
    additional_notes = models.TextField(blank=True)
    photos = models.ManyToManyField('CheckoutPhoto', blank=True)
    
    is_completed = models.BooleanField(default=False)

    def __str__(self):
        return f"Checkout Inventory for {self.reservation}"

class CheckoutPhoto(models.Model):
    image = models.ImageField(upload_to='checkout_photos/')
    description = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.description



class Incident(models.Model):
    INCIDENT_TYPES = [
        ('PANNE', 'Panne'),
        ('DOMMAGE', 'Dommage'),
        ('FUITE', 'Fuite'),
        ('DEGRADATION', 'Dégradation'),
        ('AUTRE', 'Autre'),
    ]

    STATUS_CHOICES = [
        ('OUVERT', 'Ouvert'),
        ('EN_COURS', 'En cours'),
        ('RESOLU', 'Résolu'),
        ('FERME', 'Fermé'),
    ]

    title = models.CharField(max_length=100, )

    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='incidents')  # Nouvelle ligne
    reported_by = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='reported_incidents')
    assigned_to = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_incidents')
    type = models.CharField(max_length=20, choices=INCIDENT_TYPES)
    description = models.TextField()
    date_reported = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OUVERT')
    resolution_notes = models.TextField(blank=True)
    resolved_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.get_type_display()} - {self.status} - {self.property.name} - {self.date_reported}"
    
    """ 
    es frais annexes dans un système de conciergerie, nous pouvons créer un modèle AdditionalExpense 
    qui sera lié à chaque propriété. 
    Nous définissons un modèle AdditionalExpense qui est lié à une propriété et inclut le type de dépense, 
    le montant, la date et une description.
    """

class AdditionalExpense(models.Model):
    EXPENSE_TYPES = [
        ('supplies', 'Fournitures'),
        ('repairs', 'Réparations'),
        ('cleaning', 'Ménage'),
        ('Assurance', 'Assurance'),
        ('Internet', 'Internet'),
        ('other', 'Autre'),
    ]

    property = models.ForeignKey('Property', on_delete=models.CASCADE, related_name='additional_expenses')
    expense_type = models.CharField(max_length=20, choices=EXPENSE_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    description = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.get_expense_type_display()} pour {self.property.name} - {self.amount}€"

