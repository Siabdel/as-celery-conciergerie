from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
# celery
from django_celery_beat.models import PeriodicTask, IntervalSchedule
from schedule.models import Calendar, Event
from django.db.models import Count, Sum
from django.utils.html import format_html
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from import_export import resources, fields, widgets
from conciergerie.models import Property 
from staff.models import Employee, Absence, Service
from django.core.exceptions import PermissionDenied
from django.utils.timezone import now
from django.contrib.auth import get_user_model
from django import forms
from django.db.models import Q

# Register your models here.

User = get_user_model()


class EmployeeForm(forms.ModelForm):
    """Formulaire qui filtre la liste des users par agence."""
    class Meta:
        model = Employee
        fields = ("user", "role", "phone_number", "work_on_saturday", "work_on_sunday")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # on limite la liste déroulante user
        if "user" in self.fields:
            try :
                agency = self.current_user.employee.agency
                self.fields["user"].queryset = User.objects.filter(
                    Q(employee__agency=agency) | Q(properties_owned__agency=agency)
                ).distinct()
            except Employee.DoesNotExist:
                pass



@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    form = EmployeeForm
    list_display = ("user_full_name", 'agency', 'get_calendar_name', 'role', 'phone_number', 'is_active', 'created_at')
    search_fields = ("user_full_name",)
    list_filter = ("agency", "role")
    readonly_fields = ("agency",)   # ← pas de liste déroulante
    
    readonly_fields = ("user_full_name",)

    def user_full_name(self, obj):
        return obj.user.get_full_name()
    user_full_name.short_description = "Nom complet"
    

    def get_calendar_name(self, obj):
        return obj.calendar.name if obj.calendar else "Pas de calendrier"
    get_calendar_name.short_description = 'Calendrier'
    
  
   # ------------------------------------------------------------------
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.current_user = request.user              # passe l’utilisateur au formulaire
        return form
    
    def save_model(self, request, obj, form, change):
        if not change:                       # création uniquement
            if request.user.is_superuser:
                # super-user : on prend l’agence du **premier** bien qu’il voit
                first = Property.objects.first()
                obj.agency = first.agency if first else None
            elif hasattr(request.user, "employee"):
                # collaborateur : son propre employeur
                obj.agency = request.user.employee.agency
            else:
                raise PermissionDenied("Vous n’êtes rattaché à aucune agence.")
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # collaborateur : uniquement les employees de son agence
        try:
            if hasattr(request.user, "employee"):
                return qs.filter(agency=request.user.employee.agency)
        
        except staff_models.Employee.DoesNotExist:
            pass
        
        return qs.none()

@admin.register(Absence)
class AbsenceAdmin(admin.ModelAdmin):
    list_display = ('get_employee', 'start_date', 'end_date', 'type_absence', )
    list_filter = ('start_date', )
    search_fields = ('employee',)
    
    def get_employee(self, obj):
        return obj.employee
   
   

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'price_display', 'duration_display', 'allow_rescheduling', 'color_preview', 'created_at')
    list_filter = ('allow_rescheduling', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at', 'color_preview')
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'image')
        }),
        (_('Pricing and Duration'), {
            'fields': ('price', 'down_payment', 'currency', 'duration')
        }),
        (_('Appearance'), {
            'fields': ('background_color', 'color_preview')
        }),
        (_('Scheduling Options'), {
            'fields': ('allow_rescheduling', 'reschedule_limit')
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def price_display(self, obj):
        return f"{obj.price} {obj.currency}"
    price_display.short_description = _("Price")

    def duration_display(self, obj):
        minutes, seconds = divmod(obj.duration.total_seconds(), 60)
        hours, minutes = divmod(minutes, 60)
        if hours:
            return f"{int(hours)}h {int(minutes)}m"
        else:
            return f"{int(minutes)}m"
    duration_display.short_description = _("Duration")

    def color_preview(self, obj):
        if obj.background_color:
            return format_html(
                '<div style="background-color: {}; width: 30px; height: 30px; border: 1px solid #000;"></div>',
                obj.background_color
            )
        return "-"
    color_preview.short_description = _("Color")

    def save_model(self, request, obj, form, change):
        if not obj.background_color:
            obj.background_color = generate_rgb_color()
        super().save_model(request, obj, form, change)

# Si la fonction generate_rgb_color n'est pas définie dans votre modèle, vous pouvez l'ajouter ici :
import random

def generate_rgb_color():
    return f"rgb({random.randint(0, 255)}, {random.randint(0, 255)}, {random.randint(0, 255)})"