from django.db import models
from core.models import ASBaseTimestampMixin, BaseImage, ResaStatus, PlatformChoices, TaskTypeService
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from django.contrib.auth import models as auth_models
from staff.models import Employee
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models, IntegrityError
from django.contrib.auth import get_user_model
from django.db.models import Sum, F
from phonenumber_field.modelfields import PhoneNumberField
from django.core.exceptions import ValidationError
from core.models import Agency
from conciergerie.managers import ReservationManager, PropertyManager, ServiceTaskManager, PricingRuleManager

# Create your models here.

# -------------------------------------------------------------------
# CONCIERGERIE MODELS
# -------------------------------------------------------------------
# conciergerie/models.py




class PropertyImage(BaseImage):
    property = models.ForeignKey('Property', related_name="images", on_delete=models.CASCADE)
    agency = models.ForeignKey(Agency, on_delete=models.CASCADE)

    def get_absolute_url(self):
        if self.slug:
            return f"/image/{self.slug}/"
        else:
            self.slug = slugify(self.title or str(self.id))
            self.save()
            return f"/image/{self.slug}/"
    class Meta:
        verbose_name = 'Property Image'
        verbose_name_plural = 'Property Images'



class Property(ASBaseTimestampMixin):
    PROPERTY_TYPES = [
        ('apartment', 'Apartment'),
        ('house', 'House'),
        ('villa', 'Villa'),
    ]
    agency = models.ForeignKey(Agency, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=PROPERTY_TYPES)
    owner = models.ForeignKey(auth_models.User, on_delete=models.CASCADE, related_name='properties_owned')   # ← indispe
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    address = models.CharField(max_length=255)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    capacity = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)

    # Remplace le manager par défaut
    objects = PropertyManager()
        
    # Metadata
    class Meta:
        verbose_name = 'Property'
        verbose_name_plural = 'Properties'
        unique_together = ("agency", "name")

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
    agency = models.ForeignKey(Agency, on_delete=models.CASCADE)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='pricing_rules')
    start_date = models.DateField()
    end_date = models.DateField()
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2)
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
    agency = models.ForeignKey(Agency, on_delete=models.CASCADE)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='reservations')
    reservation_status = models.CharField(max_length=20, choices=ResaStatus.choices,
                                          default=ResaStatus.PENDING)
    check_in = models.DateTimeField(default=timezone.now)
    check_out = models.DateTimeField(default=timezone.now)
    guest_name = models.CharField(max_length=100)
    guest_email = models.EmailField()
    platform = models.CharField(max_length=20, choices=PlatformChoices.choices,
                                default=PlatformChoices.AIRBNB, null=True)
    number_of_guests = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    cleaning_fee = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    service_fee = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    guest_phone = models.CharField(max_length=20, blank=True)
    booking_date = models.DateTimeField(auto_now_add=True)
     # =====  NEW FIELDS  =====
    arrival_deadline = models.DateTimeField( _("Arrivée au plus tard le"), null=True, blank=True,
        help_text=_("Heure limite d'arrivée du voyageur"))
    nights = models.PositiveSmallIntegerField( _("Nb nuits"), null=True, blank=True,
        help_text=_("Calculé automatiquement si laissé vide"))
    currency = models.CharField(
        _("Devise"), max_length=3, default='EUR',
        choices=[('EUR','EUR'),('USD','USD'),('MAD','MAD')])
    amount_paid = models.DecimalField(
        _("Montant versé"), max_digits=10, decimal_places=2, default=0)
    gross_revenue = models.DecimalField(
        _("Revenus bruts"), max_digits=10, decimal_places=2, default=0)
    
    special_requests = models.TextField(blank=True)
    is_business_trip = models.BooleanField(default=False)
    guest_rating = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], null=True, blank=True)
    cancellation_policy = models.CharField(max_length=100, blank=True)
    booking_date = models.DateTimeField(auto_now_add=True)
    
    # Remplace le manager par défaut
    objects = ReservationManager()
     
    def save(self, *args, **kwargs):
        # auto-compute nights if empty
        if not self.nights and self.check_in and self.check_out:
            self.nights = (self.check_out.date() - self.check_in.date()).days
        # auto-compute gross revenue if empty
        if not self.gross_revenue:
            self.gross_revenue = self.total_price  # already calculated
        super().save(*args, **kwargs)


    class Meta:
        ordering = ("property", "check_in", )
        unique_together = ("property", "check_in", )

    def __str__(self):
        return f"Reservation for {self.property} from {self.check_in} to {self.check_out}"

    def get_duration(self):
        return (self.check_out - self.check_in).days + 1

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
    


class ServiceTaskManager(models.Manager):
    def for_user(self, user):
        if user.is_superuser:
            return self.all()
        return self.filter(property__owner=user)


class ServiceTask(ASBaseTimestampMixin):
    agency = models.ForeignKey(Agency, on_delete=models.CASCADE)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='tasks')
    employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True,
                                 related_name='tasks')
    reservation = models.ForeignKey(Reservation, null=True, on_delete=models.CASCADE,
                                    related_name='tasks')
    description = models.TextField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=ResaStatus.choices,
                              default=ResaStatus.PENDING)
    type_service = models.CharField(max_length=20, choices=TaskTypeService.choices,
                                    default=TaskTypeService.CHECKED_IN)
    completed = models.BooleanField(default=False)
    # override default manager
    objects = ServiceTaskManager()  # Remplace le manager par défaut

    def __str__(self):
        return f"Task for {self.property} - {self.end_date}"


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
    agency = models.ForeignKey(Agency, on_delete=models.CASCADE)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='incidents')
    title = models.CharField(max_length=100)
    reported_by = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='reported_incidents')
    assigned_to = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='assigned_incidents')
    type = models.CharField(max_length=20, choices=INCIDENT_TYPES)
    description = models.TextField()
    date_reported = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OUVERT')
    resolution_notes = models.TextField(blank=True)
    resolved_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.get_type_display()} - {self.status} - {self.property.name}"


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                   related_name="%(class)s_created")
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                   related_name="%(class)s_updated")

    class Meta:
        abstract = True


class AdditionalExpense(BaseModel):
    EXPENSE_TYPES = [
        ('supplies', 'Fournitures'),
        ('repairs', 'Réparations'),
        ('cleaning', 'Ménage'),
        ('assurance', 'Assurance'),
        ('internet', 'Internet'),
        ('other', 'Autre'),
    ]
    agency = models.ForeignKey(Agency, on_delete=models.CASCADE)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='additional_expenses')
    expense_type = models.CharField(max_length=20, choices=EXPENSE_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255, blank=True)
    occurrence_date = models.DateField(null=True, blank=True)
    is_recurring = models.BooleanField(default=False)
    recurrence_interval = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)
    receipt = models.FileField(upload_to='receipts/', null=True, blank=True)
    ## new fees fields
    service_fee = models.DecimalField(
        _("Frais de service"), max_digits=8, decimal_places=2, default=0)
    quick_pay_fee = models.DecimalField(
        _("Frais paiement rapide"), max_digits=8, decimal_places=2, default=0)
    cleaning_fee = models.DecimalField(
        _("Frais ménage"), max_digits=8, decimal_places=2, default=0)
    linen_fee = models.DecimalField( _("Frais linge de maison"), max_digits=8, decimal_places=2, default=0)
    incurred_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True,
                                   related_name='incurred_expenses', blank=True)
    date_incurred = models.DateField(default=timezone.now)
    

    #@property                      # ← décorateur
    def total_fees(self):          # ← méthode
        return (
            self.service_fee +
            self.quick_pay_fee +
            self.cleaning_fee +
            self.linen_fee
        )


    def save(self, *args, **kwargs):
        # optional: auto-fill amount field with sum of fees
        if self.amount == 0 and self.total_fees:
            self.amount = self.total_fees
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_expense_type_display()} pour {self.property.name} - {self.amount}€"

        
    #---------------------------------------
#-Etat des lieux du bien               -
#---------------------------------------
class CheckoutInventory(models.Model):
    agency = models.ForeignKey(Agency, on_delete=models.CASCADE)
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
    agency = models.ForeignKey(Agency, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='checkout_photos/')
    description = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.description
