from django.contrib import admin
from django.utils.html import format_html
# celery
from django_celery_beat.models import PeriodicTask, IntervalSchedule
from schedule.models import Calendar, Event
from django.db.models import Count, Sum
from django.utils.html import format_html
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from import_export import resources, fields, widgets
from services_menage import models as cg_models
from staff import models as staff_models


# Register your models here.

@admin.register(cg_models.Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_calendar_name')
    search_fields = ('name',)

    def get_calendar_name(self, obj):
        return obj.calendar.name if obj.calendar else "Pas de calendrier"
    get_calendar_name.short_description = 'Calendrier'

@admin.register(staff_models.Absence)
class AbsenceAdmin(admin.ModelAdmin):
    list_display = ('get_employee', 'start_date', 'end_date', 'type_absence', )
    list_filter = ('start_date', )
    search_fields = ('employee',)
    
    def get_employee(self, obj):
        return obj.employee
   