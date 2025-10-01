import colorsys
import datetime
import random
import string
import uuid
from decimal import Decimal, InvalidOperation

from babel.numbers import get_currency_symbol
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator, MinLengthValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField
from django.contrib.auth.models import User
from core.models import CustomCalendar
from core.models import Agency 

PAYMENT_TYPES = (
    ('full', _('Full payment')),
    ('down', _('Down payment')),
)

DAYS_OF_WEEK = (
    (0, 'Sunday'),
    (1, 'Monday'),
    (2, 'Tuesday'),
    (3, 'Wednesday'),
    (4, 'Thursday'),
    (5, 'Friday'),
    (6, 'Saturday'),
)


def generate_rgb_color():
    hue = random.random()  # Random hue between 0 and 1
    saturation = 0.9  # High saturation to ensure a vivid color
    value = 0.9  # High value to ensure a bright color

    r, g, b = colorsys.hsv_to_rgb(hue, saturation, value)

    # Convert to 0-255 RGB values
    r = int(r * 255)
    g = int(g * 255)
    b = int(b * 255)

    return f'rgb({r}, {g}, {b})'



class Service(models.Model):
    """
    Represents a service provided by the appointment system.

    Author: Adams Pierre David
    Version: 1.1.0
    Since: 1.0.0
    """
    agency = models.ForeignKey(Agency, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, blank=False)
    description = models.TextField(blank=True, null=True)
    duration = models.DurationField(validators=[MinValueValidator(datetime.timedelta(seconds=1))])
    price = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)])
    down_payment = models.DecimalField(max_digits=6, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    image = models.ImageField(upload_to='upload/', blank=True, null=True)
    currency = models.CharField(max_length=3, default='MAD', validators=[MaxLengthValidator(3), MinLengthValidator(3)])
    background_color = models.CharField(max_length=50, null=True, blank=True, default=generate_rgb_color)
    reschedule_limit = models.PositiveIntegerField(
        default=0,
        help_text=_("Maximum number of times an appointment can be rescheduled.")
    )
    allow_rescheduling = models.BooleanField(
        default=False,
        help_text=_("Indicates whether appointments for this service can be rescheduled.")
    )

    # meta data
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "price": str(self.price)  # Convert Decimal to string for JSON serialization
        }

    def get_duration_parts(self):
        total_seconds = int(self.duration.total_seconds())
        days = total_seconds // 86400
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return days, hours, minutes, seconds

    def get_duration(self):
        days, hours, minutes, seconds = self.get_duration_parts()
        parts = []

        if days:
            parts.append(f"{days} day{'s' if days > 1 else ''}")
        if hours:
            parts.append(f"{hours} hour{'s' if hours > 1 else ''}")
        if minutes:
            parts.append(f"{minutes} minute{'s' if minutes > 1 else ''}")
        if seconds:
            parts.append(f"{seconds} second{'s' if seconds > 1 else ''}")

        return ' '.join(parts)

    def get_price(self):
        # Check if the decimal part is 0
        if self.price % 1 == 0:
            return int(self.price)  # Return as an integer
        else:
            return self.price  # Return the original float value

    def get_currency_icon(self):
        return get_currency_symbol(self.currency, locale=get_locale())

    def get_price_text(self):
        if self.price == 0:
            return "Free"
        else:
            return f"{self.get_price()}{self.get_currency_icon()}"

    def get_down_payment(self):
        if self.down_payment % 1 == 0:
            return int(self.down_payment)  # Return as an integer
        else:
            return self.down_payment  # Return the original float value

    def get_down_payment_text(self):
        if self.down_payment == 0:
            return f"Free"
        return f"{self.get_down_payment()}{self.get_currency_icon()}"

    def get_image_url(self):
        if not self.image:
            return ""
        return self.image.url

    def is_a_paid_service(self):
        return self.price > 0

    def accepts_down_payment(self):
        return self.down_payment > 0


     


class Employee(models.Model):
    ROLE_CHOICES = [
        ('cleaner', 'Cleaner'),
        ('maintenance', 'Maintenance'),
        ('concierge', 'Concierge'),
        ('manager', 'Manager'),
    ]
    agency = models.ForeignKey(Agency, on_delete=models.CASCADE) # new field
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="employee")
    calendar = models.ForeignKey(CustomCalendar, on_delete=models.CASCADE, null=True, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='cleaner')
    phone_number = models.CharField(max_length=15, null=True)
    hire_date = models.DateField( null=True, blank=True ) # date d'embauche
    is_active = models.BooleanField(default=True)
    services_offered = models.ManyToManyField(Service)
    slot_duration = models.PositiveIntegerField(
        null=True, blank=True,
        help_text=_("Minimum time for an appointment in minutes, recommended 30.")
    )
    work_on_saturday = models.BooleanField(default=False)
    work_on_sunday = models.BooleanField(default=False)
    # meta data
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        ## return f"{self.get_staff_member_name()}"
        return f"{self.agency} - {self.user} - {self.get_role_display()}"



    def get_slot_duration(self):
        config = Config.objects.first()
        return self.slot_duration or (config.slot_duration if config else 0)
    
    def get_lead_time(self):
        config = Config.objects.first()
        return self.lead_time or (config.lead_time if config else None)

   
    def works_on_both_weekends_day(self):
        return self.work_on_saturday and self.work_on_sunday

    def get_staff_member_name(self):
        name_options = [
            getattr(self.user, 'get_full_name', lambda: '')(),
            f"{self.user.first_name} {self.user.last_name}",
            self.user.username,
            self.user.email,
            f"Staff Member {self.id}"
        ]
        return next((name.strip() for name in name_options if name.strip()), "Unknown")

    def get_staff_member_first_name(self):
        return self.user.first_name

    def get_non_working_days(self):
        non_working_days = []

        if not self.work_on_saturday:
            non_working_days.append(6)  # Saturday
        if not self.work_on_sunday:
            non_working_days.append(0)  # Sunday
        return non_working_days

    def get_weekend_days_worked_text(self):
        if self.work_on_saturday and self.work_on_sunday:
            return _("Saturday and Sunday")
        elif self.work_on_saturday:
            return _("Saturday")
        elif self.work_on_sunday:
            return _("Sunday")
        else:
            return _("None")

    def get_services_offered(self):
        return self.services_offered.all()

    def get_service_offered_text(self):
        return ', '.join([service.name for service in self.services_offered.all()])

    def get_service_is_offered(self, service_id):
        return self.services_offered.filter(id=service_id).exists()

  
    def get_days_off(self):
        return DayOff.objects.filter(staff_member=self)

    def get_working_hours(self):
        return self.workinghours_set.all()

    def update_upon_working_hours_deletion(self, day_of_week: int):
        if day_of_week == 6:
            self.work_on_saturday = False
        elif day_of_week == 0:
            self.work_on_sunday = False
        self.save()

    def is_working_day(self, day: int):
        return day not in self.get_non_working_days()



class Absence(models.Model):
    class TypeAbsence(models.TextChoices):
        CONGES = 'CONG', _('En conges')
        MALADIE = 'MALD', _('En maladie')
        INCONNU = 'NJSU', _('Non justifier')
    
    agency = models.ForeignKey(Agency, on_delete=models.CASCADE)
    type_absence = models.CharField(max_length=200, 
                                    choices=TypeAbsence.choices,
                                    default=TypeAbsence.INCONNU)

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    description = models.CharField(max_length=254, blank=True, null=True)
    # meta data
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.start_date} to {self.end_date} - {self.description if self.description else 'Day off'}"

    def clean(self):
        if self.start_date is not None and self.end_date is not None:
            if self.start_date > self.end_date:
                raise ValidationError(_("Start date must be before end date"))

    def is_owner(self, user_id):
        return self.staff_member.user.id == user_id

