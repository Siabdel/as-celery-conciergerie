# Register your models here.
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from django.contrib import messages
from django.db.models import Count, Sum
from django.utils.html import format_html
from .models import Reservation, Employee, MaintenanceTask, Property   
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
        new_reservation = Reservation.objects.create(
            client=reservation.client,
            check_in=reservation.check_in,
            check_out=reservation.check_out,
            # Ajoutez ici d'autres champs si nécessaire
        )
        # Vous pouvez personnaliser le nouveau titre si vous le souhaitez
        new_reservation.client = f"Copie de {new_reservation.client}"
        new_reservation.save()
    
    messages.success(request, _(f"{queryset.count()} réservation(s) dupliquée(s) avec succès."))


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('property', 'guest_name', 'start_date', 'end_date', 'reservation_status', 'total_price')
    list_filter = ('reservation_status', 'property', 'start_date')
    search_fields = ('guest_name', 'guest_email', 'property__name')
    date_hierarchy = 'start_date'
    actions = [duplicate_reservation]  # Ajoutez l'action ici
   
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

@admin.register(MaintenanceTask)
class MaintenanceTaskAdmin(admin.ModelAdmin):
    list_display = ('get_client', 'employee', 'due_date')
    #list_filter = ('scheduled_time', 'employee')
    search_fields = ('reservation__client', 'employee__name')

    def get_client(self, obj):
        return obj.reservation.client
    get_client.short_description = 'Client'

# Personnalisation de l'admin pour Calendar et Event
class CalendarAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug')
    search_fields = ('name', 'slug')

class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'start', 'end', 'calendar')
    list_filter = ('start', 'end', 'calendar')
    search_fields = ('title',)


# Réenregistrement des modèles de django-scheduler avec notre configuration personnalisée
admin.site.unregister
