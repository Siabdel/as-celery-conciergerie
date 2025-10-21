from django.contrib.auth import get_user_model

import os
from django.db import models, IntegrityError
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User, AbstractUser, UserManager
from django.utils import timezone
from core.utils import make_thumbnail
from django.conf import settings
from django.db.models import Sum, F
from django.utils.text import slugify
from icalendar import Calendar, Event
from datetime import datetime, timedelta
import pytz
import uuid
from django.conf import settings


# -------------------------------------------------------------------
# CORE MODELS
# -------------------------------------------------------------------

"""_summary_
    Pour transformer votre Django-Conciergerie en SaaS B2B multi-agences il suffit d’ajouter 
UNE seule table racine : Agency (ou Company) et de toutes faire pointer dessus via ForeignKey.
Le reste du code (vues, API, admin) devient multi-tenant en filtrant 
systématiquement par request.user.agency.

"""

class AbstractBaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name='%(class)s_created_by')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name='%(class)s_updated_by')

    class Meta:
        abstract = True


class Agency(AbstractBaseModel):
    CURRENCY_CHOICES = [
        ('USD', 'US Dollar'),
        ('EUR', 'Euro'),
        ('GBP', 'British Pound'),
        ('JPY', 'Japanese Yen'),
    ]
    name = models.CharField(max_length=200)
    code = models.SlugField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    slug        = models.SlugField(max_length=100, unique=True, blank=True)  # blank=True permet vide en admin
    logo        = models.ImageField(upload_to="agency/logos/", blank=True)
    
    currency    = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default="EUR")
    is_active   = models.BooleanField(default=False)
    president_name = models.CharField(max_length=100, blank=True, null=True)
    address     = models.CharField(max_length=255, blank=True, null=True)
    class Meta:
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['code']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:                      # pas de slug fourni
            self.slug = slugify(self.name)     # généré depuis name
        super().save(*args, **kwargs)
    
class AbstractTenantModel(AbstractBaseModel):
    agency = models.ForeignKey(Agency, on_delete=models.CASCADE, related_name="%(class)s_set")

    class Meta:
        abstract = True
        indexes = [ models.Index(fields=["agency"]), ]


# core/models.py (ajout)

# core/models.py
from django.db import models
from django.utils.html import mark_safe

class LandingSection(models.Model):
    """Éléments de la page d’accueil publique."""
    title = models.CharField("Titre", max_length=200)
    subtitle = models.CharField("Sous-titre", max_length=300, blank=True)
    description = models.TextField("Description")
    icon = models.CharField(
        "Icône Bootstrap",
        max_length=50,
        blank=True,
        help_text="Ex: 'bi bi-gear', 'bi bi-lightning-charge-fill'"
    )
    image = models.ImageField("Image illustrée", upload_to="landing/", blank=True, null=True)
    is_active = models.BooleanField("Visible sur la page", default=True)
    order = models.PositiveIntegerField("Ordre d’affichage", default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order"]
        verbose_name = "Section de la page d’accueil"
        verbose_name_plural = "Sections de la page d’accueil"

    def __str__(self):
        return self.title

    def image_preview(self):
        if self.image:
            return mark_safe(f'<img src="{self.image.url}" width="100" style="border-radius:8px;" />')
        return "(Aucune image)"
    image_preview.short_description = "Aperçu"




class CustomUser(AbstractUser):
    """
    Modèle utilisateur unique pour le système SaaS.
    Gère les rôles, rattachement agence, et logique propriétaire/employé.
    """
    class Roles(models.TextChoices):
        SUPERADMIN = "superadmin", "Super administrateur (SaaS)"
        AGENCY_ADMIN = "agency_admin", "Administrateur d'agence"
        OWNER = "owner", "Propriétaire"
        EMPLOYEE = "employee", "Employé"
        CLIENT = "client", "Client / locataire"

    agency = models.ForeignKey(
        "core.Agency", on_delete=models.CASCADE,
        related_name="users", null=True, blank=True
    )
    role = models.CharField(max_length=20, choices=Roles.choices, default=Roles.CLIENT)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        agency_name = self.agency.name if self.agency else "—"
        return f"{self.username} ({self.role}) [{agency_name}]"

    @property
    def is_agency_admin(self):
        return self.role == self.Roles.AGENCY_ADMIN

    @property
    def is_owner(self):
        return self.role == self.Roles.OWNER

    @property
    def is_employee(self):
        return self.role == self.Roles.EMPLOYEE

    def as_role(self):
        """Retourne une instance enrichie du comportement correspondant au rôle.
        user = request.user.as_role()
        if hasattr(user, "get_assigned_tasks"):
        tasks = user.get_assigned_tasks()
        """
        role_map = {
            self.Roles.AGENCY_ADMIN: AgencyAdminMixin,
            self.Roles.EMPLOYEE: EmployeeMixin,
            self.Roles.OWNER: OwnerMixin,
        }
        base_class = role_map.get(self.role)
        if base_class:
            # Crée dynamiquement une instance mixée
            class RoleUser(self.__class__, base_class):
                pass
            return RoleUser.objects.get(pk=self.pk)
        return self
    class Meta:
        indexes = [
            models.Index(fields=["agency", "role"]),
            models.Index(fields=["username"]),
            models.Index(fields=["email"]),
        ]

class ReservationStatus(models.TextChoices):
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
    NEED_ATTENTION = 'NEED_ATTENTION', _('Needs Attention')
    IN_PROGRESS = 'IN_PROGRESS', _('In Progress')
    COMPLETED = 'COMPLETED', _('Completed')
    CONFIRMED = 'CONFIRMED', _('Confirmed')
    CHECKED_IN = 'CHECKIN', _('Checked In')
    CHECKED_OUT= 'CHECKOUT', _('Checked Out')
    CANCELLED = 'CANCEL', _('Cancelled')
    EXPIRED = 'EXPIRED', _('Expired')
    NEEDS_ATTENTION = 'NEEDS_ATTENTION', _('Needs Attention')

    
class PlatformChoices(models.TextChoices) :
    AIRBNB = 'AIRBNB', _('Airbnb')
    BOOKING = 'BOOKING', _('Booking')
    DIRECT = 'DIRECT' , _('Direct Booking')
    
 
class TaskTypeService(models.TextChoices):
    CHECKED_IN = 'CHECKIN', _('Checked In')
    CHECKED_OUT= 'CHECKOUT', _('Checked Out')
    CLEANING = 'CLEAN', _('Cleaning')
    MAINTENANCE = 'MAINTENANCE', _('Maintenance')
    ERROR = 'ERROR', _('Error')


  

class BaseImage(AbstractTenantModel):
    class Meta:
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['created_at']),
        ]
    title = models.CharField(_('Titre'), max_length=50, null=True, blank=True)
    slug = models.SlugField(max_length=255, db_index=True, null=True, blank=True)
    image = models.ImageField(upload_to='upload/product_images/%Y/%m/', blank=True)
    thumbnail_path = models.CharField(_("thumbnail"), max_length=255, null=True, blank=True)
    large_path = models.CharField(_("large"), max_length=255, null=True, blank=True)


    def save(self, *args, **kwargs):
        #raise Exception(f"args {args} kwargs = {kwargs}")
        if self.image:
            img_100 = make_thumbnail(self.image, size=(100, 100))
            img_800 = make_thumbnail(self.image, size=(800, 600))
           
            output_dir = os.path.join(settings.MEDIA_ROOT, "media")
            # Enregistre les images traitées
            base_name = os.path.basename(img_100.name)
            self.thumbnail_path = os.path.join(output_dir, f"thumb_100x100_{base_name}")

            base_name = os.path.basename(img_800.name)
            self.large_path = os.path.join(output_dir, f"large_800x600_{base_name}")
        
        super().save(*args, **kwargs)
        
    def __str__(self):
        return f"Image for {self.image.name}"

    class Meta:
        abstract = True
        
   
    def get_absolute_url(self):
        """
        Hook for returning the canonical Django URL of this product.
        """
        msg = "Method get_absolute_url() must be implemented by subclass: `{}`"
        raise NotImplementedError(msg.format(self.__class__.__name__))

    class Meta:
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['updated_at']),
        ]

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


class CustomCalendar(AbstractTenantModel):
    """
    Représente un calendrier iCalendar pour un employé.
    Chaque agence / employé a son propre .ics exportable.
    """
    employee = models.OneToOneField("staff.Employee", on_delete=models.CASCADE, related_name="employee_calendar")
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100)
    description = models.TextField(blank=True)
    last_generated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.agency.name})"
    
    def save(self, *args, **kwargs):
        if not self.slug:                      # pas de slug fourni
            self.slug = slugify(self.name)     # généré depuis name
        super().save(*args, **kwargs)
    

    def generate_ical(self):
        """
        Génère un objet iCalendar (.ics) contenant les tâches de l’employé.
        """
        cal = Calendar()
        cal.add("prodid", "-//Conciergerie SaaS//EN")
        cal.add("version", "2.0")
        cal.add("X-WR-CALNAME", self.name)
        cal.add("X-WR-TIMEZONE", "Europe/Paris")

        # On va chercher les tâches de l’employé
        tasks = self.employee.tasks.all().select_related("property")

        for task in tasks:
            event = Event()
            event.add("uid", str(uuid.uuid4()))
            event.add("summary", f"{task.type_service} - {task.property.name}")
            event.add("description", task.description)
            event.add("dtstart", task.start_date)
            event.add("dtend", task.end_date)
            event.add("dtstamp", timezone.now())
            event.add("status", "CONFIRMED" if task.completed else "TENTATIVE")
            event.add("location", getattr(task.property, "address", ""))
            cal.add_component(event)

        return cal

    def export_to_file(self, filepath=None):
        """
        Sauvegarde le .ics dans un fichier local (ex: pour téléchargement ou envoi email)
        """
        cal = self.generate_ical()
        ics_data = cal.to_ical()

        if not filepath:
            filepath = f"media/calendars/{self.employee.id}_{self.agency.id}.ics"

        with open(filepath, "wb") as f:
            f.write(ics_data)
        return filepath

    def export_to_http_response(self):
        """
        Retourne la réponse HTTP pour téléchargement du .ics via API
        """
        from django.http import HttpResponse
        cal = self.generate_ical()
        response = HttpResponse(cal.to_ical(), content_type="text/calendar")
        response["Content-Disposition"] = f'attachment; filename="{self.employee.name}.ics"'
        return response

    """ 
    @classmethod
    def create_unique(cls, name, slug):
        if not cls.objects.filter(name=name).exists():
            return cls.objects.create(name=name, slug=slug)
        return cls.objects.get(name=name)
        if not cls.objects.filter(name=name).exists():
            return cls.objects.create(name=name, slug=slug)
        return cls.objects.get(name=name)
    """


