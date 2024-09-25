# Register your models here.
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from .models import Reservation, Employee, CleaningTask
from schedule.models import Calendar, Event

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

class ReservationAdmin(admin.ModelAdmin):
    list_display = ('client', 'check_in', 'check_out')
    list_filter = ('check_in', 'check_out')
    search_fields = ('client',)
    actions = [duplicate_reservation]  # Ajoutez l'action ici

class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_calendar_name')
    search_fields = ('name',)

    def get_calendar_name(self, obj):
        return obj.calendar.name if obj.calendar else "Pas de calendrier"
    get_calendar_name.short_description = 'Calendrier'

class CleaningTaskAdmin(admin.ModelAdmin):
    list_display = ('get_client', 'employee', 'scheduled_time')
    list_filter = ('scheduled_time', 'employee')
    search_fields = ('reservation__client', 'employee__name')

    def get_client(self, obj):
        return obj.reservation.client
    get_client.short_description = 'Client'

# Personnalisation de l'admin pour Calendar et Event
class CalendarAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'start', 'end', 'calendar')
    list_filter = ('start', 'end', 'calendar')
    search_fields = ('title',)

admin.site.register(Reservation, ReservationAdmin)
admin.site.register(Employee, EmployeeAdmin)
admin.site.register(CleaningTask, CleaningTaskAdmin)

# Réenregistrement des modèles de django-scheduler avec notre configuration personnalisée
admin.site.unregister
