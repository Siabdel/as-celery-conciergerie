# Register your models here.
from django.contrib import admin
import json
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.db.models import Count, Sum
from django.db import models, IntegrityError
from django.core.exceptions import ValidationError
from django.utils.html import format_html
from .models import Reservation, Employee, ServiceTask, Property, Absence   
# celery
from django.utils.timezone import now
from django_celery_beat.models import PeriodicTask, IntervalSchedule
from .models import Reservation
from .tasks import service_menage_task
##
from schedule.models import Calendar, Event

@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'address', 'owner', 'reservation_count', 'total_revenue')
    list_filter = ('type', 'owner')
    search_fields = ('name', 'address')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(owner=request.user)

    def reservation_count(self, obj):
        return obj.reservations.all().count()
    reservation_count.short_description = 'Réservations'

    
    # Dans votre méthode ou fonction
    def total_revenue(self, obj):
        total = obj.reservations.aggregate(Sum('total_price'))['total_price__sum']
        formatted_total = f'${total:.2f}' if total else '$0.00'
        return format_html('{}'.format(formatted_total))
    #
    total_revenue.short_description = 'Revenu Total'


@admin.action(description=_("Dupliquer les réservations sélectionnées"))
def duplicate_reservation(modeladmin, request, queryset):
    for reservation in queryset:
        # Créer une nouvelle réservation avec les mêmes données
        try :
            new_reservation = Reservation.objects.create(
                property = reservation.property,
                check_in = now(),
                check_out =  now(),
                reservation_status = "Pending",
                # Ajoutez ici d'autres champs si nécessaire
            )
            #
            messages.success(request, _(f"{queryset.count()} réservation(s) dupliquée(s) avec succès."))
            ##new_reservation.save()
        except ValidationError as err:
            messages.error(request, "## Erreur ###" + str(err))
        #


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('property', 'guest_name', 'check_in', 'check_out', 'reservation_status', 'total_price')
    list_filter = ('reservation_status', 'property', 'check_in')
    search_fields = ('guest_name', 'guest_email', 'property__name')
    date_hierarchy = 'check_in'
    actions = [duplicate_reservation]  # Ajoutez l'action ici
    
    def save_model(self, request, obj, form, change):
        try:
            obj.save()
        except ValidationError as err:
            messages.error(request, str(err))
   
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(property__owner=request.user)

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)
        
        try:
            qs = response.context_data['cl'].queryset
        except (AttributeError, KeyError):
            return response

        metrics = {
            'total': Count('id'),
            'total_revenue': Sum('total_price'),
        }

        response.context_data['summary'] = list(
            qs.values('reservation_status').annotate(**metrics).order_by('reservation_status')
        )

        return response


    actions = [duplicate_reservation]  # Ajoutez l'action ici

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_calendar_name')
    search_fields = ('name',)

    def get_calendar_name(self, obj):
        return obj.calendar.name if obj.calendar else "Pas de calendrier"
    get_calendar_name.short_description = 'Calendrier'

@admin.register(ServiceTask)
class ServiceTaskAdmin(admin.ModelAdmin):
    list_display = ('get_description', 'get_client', 'get_guestname',
                    'employee', 'start_date', 'end_date', 'reservation', )
    #list_filter = ('scheduled_time', 'employee')
    search_fields = ('property__client', 'employee__name')
    list_filter = ('property', 'employee', 'start_date')

    def get_client(self, obj):
        return obj.property
    get_client.short_description = 'Client'
    
    def get_description(self, obj):
        return obj.description[:20]
    
    def get_guestname(self, obj):
        # ServiceTask.objects.filter(reservation__guest_name__isnull=True).exists()
        return obj.reservation.guest_name if obj.reservation else 'No guest name'
      

# Personnalisation de l'admin pour Calendar et Event
class CalendarAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug', )
    search_fields = ('name', 'slug')


class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'start', 'end', 'calendar')
    list_filter = ('start', 'end', 'calendar')
    search_fields = ('title',)

@admin.register(Absence)
class AbsenceAdmin(admin.ModelAdmin):
    list_display = ('get_employee', 'start_date', 'end_date', 'type_absence', )
    list_filter = ('start_date', )
    search_fields = ('employee',)
    
    def get_employee(self, obj):
        return obj.employee
        
    
    
# Réenregistrement des modèles de django-scheduler avec notre configuration personnalisée
admin.site.unregister
admin.register(Event, EventAdmin)

