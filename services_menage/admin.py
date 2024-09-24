# Register your models here.
from django.contrib import admin
from .models import Reservation, Employee, CleaningTask
from schedule.models import Calendar, Event

class ReservationAdmin(admin.ModelAdmin):
    list_display = ('client', 'check_in', 'check_out')
    list_filter = ('check_in', 'check_out')
    search_fields = ('client',)

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
