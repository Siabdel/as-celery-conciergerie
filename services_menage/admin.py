# Register your models here.
import json
from django.contrib import admin
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.db.models import Count, Sum
from django.db import models, IntegrityError
from django.core.exceptions import ValidationError
from django.utils.html import format_html
from services_menage import models as sm_models
from staff import models as staff_models
# celery
from django_celery_beat.models import PeriodicTask, IntervalSchedule
from schedule.models import Calendar, Event
from django.db.models import Count, Sum
from django.utils.html import format_html
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from import_export import resources, fields, widgets
from django.contrib.admin import StackedInline
from .models import Property, PropertyImage, Incident
from core.models import BaseImage


@admin.register(PropertyImage)
class PropertyImageAdmin(admin.ModelAdmin):
    list_display =  [field.name for field in PropertyImage._meta.get_fields()]

@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = ('property', 'type', 'title', 'status_tag', 'date_reported', 'reported_by', 'assigned_to')
    readonly_fields = ('date_reported', 'reported_by')
    list_filter = ('type', 'status', 'property', 'date_reported')
    search_fields = ('description', 'reported_by__name', 'assigned_to__name', 'property__name')
    
    fieldsets = (
        (None, {
            'fields': ('type', 'description', 'status')
        }),

        ('Informations de rapport', {
            'fields': ('date_reported', 'reported_by'),
            'classes': ('collapse',)
        }),
        ('Attribution', {
            'fields': ('assigned_to',)
        }),
        ('Résolution', {
            'fields': ('resolution_notes', 'resolved_date')
        }),
       
    )

    def save_model(self, request, obj, form, change):
        if not change:  # Si c'est un nouvel incident
            obj.reported_by = Employee.objects.get(user=request.user)
        
        if obj.status == 'RESOLU' and not obj.resolved_date:
            obj.resolved_date = timezone.now()
        
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.GET.get('status__exact') == 'EN_COURS':
            return qs.filter(status='EN_COURS')
        return qs
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "assigned_to":
            kwargs["queryset"] = Employee.objects.filter(role__in=['maintenance', 'concierge', 'manager'])
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    actions = ['mark_as_resolved']

    def mark_as_resolved(self, request, queryset):
        updated = queryset.update(status='RESOLU', resolved_date=timezone.now())
        self.message_user(request, f'{updated} incident(s) marqué(s) comme résolu(s).')
    mark_as_resolved.short_description = "Marquer les incidents sélectionnés comme résolus"

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_unresolved'] = request.GET.get('unresolved', False)
        return super().changelist_view(request, extra_context=extra_context)

    def status_tag(self, obj):
        if obj.status == 'EN_COURS':
            return format_html('<span style="background-color: red; color: white; padding: 3px; border-radius: 3px;">En cours</span>')
        return obj.get_status_display()
# Register your models here.
class PropertyImageInline(StackedInline):
    model = PropertyImage
    readonly_fields = ('thumbnail_path', 'large_path',)
    fieldsets = (('System Images', {
                'fields': (
                    ('title', 'image'),
                ),
                'classes': ('collapse',)
            })),
    extra = 0
    
class PropertyIncidentInline(admin.TabularInline):
    model = Incident
    fieldsets = (('ticket Incidents', {
                'fields': (
                    'title',
                    ('type', 'status', 'reported_by', 'assigned_to')
                ),
                'classes': ('collapse',)
            })),
    extra = 0


class PricingRuleInline(admin.TabularInline):
    model = sm_models.PricingRule
    extra = 0

 
class AdditionalExpenseInline(admin.TabularInline):
    model = sm_models.AdditionalExpense
    extra = 0
    fields = ('property', 'expense_type', 'amount', 'description',)
    exclude = ('created_at', 'updated_at', 'created_by', 'updated_by',)
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by',)
    show_change_link = True
    
@admin.register(sm_models.AdditionalExpense)
class AdditionalExpenseAdmin(admin.ModelAdmin):
    list_display = ('property', 'expense_type', 'amount', )
    list_filter = ('expense_type', 'property', )
    search_fields = ('property__name', 'description')
    exclude = ('created_at', 'updated_at', 'created_by', 'updated_by',)
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by',)
    show_change_link = True

    def save_model(self, request, obj, form, change):
        if not change:  
            obj.created_by = request.user
        if not obj.created_by :
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
        
@admin.register(sm_models.Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'owner', 'price_per_night_display', 'address_preview')
    list_filter = ('type', 'owner')
    search_fields = ('name', 'address', 'owner__username')
    readonly_fields = ('created_at', 'updated_at', 'created_by')
    inlines = [PricingRuleInline, PropertyImageInline, PropertyIncidentInline, AdditionalExpenseInline]

    fieldsets = (
        ('Property Information', {
            'fields': (
                'name',
                ('type', 'owner'),
                'price_per_night',
            )
        }),
        ('Location', {
            'fields': ('address',),
        }),
        ('System Information', {
            'fields': (
                ('created_at', 'updated_at'),
                'created_by',
            ),
            'classes': ('collapse',)
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ('created_by',)
        return self.readonly_fields

    def price_per_night_display(self, obj):
        return format_html('<span style="color: green; font-weight: bold;">${}</span>', obj.price_per_night)
    price_per_night_display.short_description = 'Price per Night'

    def address_preview(self, obj):
        return obj.address[:50] + '...' if len(obj.address) > 50 else obj.address
    address_preview.short_description = 'Address Preview'

    def save_model(self, request, obj, form, change):
        if not change:  # if creating a new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
 
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

@admin.register(sm_models.PricingRule)
class PricingRuleAdmin(admin.ModelAdmin):
    list_display = ('property', 'start_date', 'end_date', 'price_per_night', 'is_active', 'priority')
    #fields = ('property', 'start_date', 'end_date', 'price_per_night',  'priority')
    list_filter = ('property',  'start_date', 'end_date')
    search_fields = ('property__name',)



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


class ReservationResource(resources.ModelResource):
    property_name = fields.Field(column_name='property_name', 
                                 attribute='property', 
                                 widget=widgets.ForeignKeyWidget(sm_models.Property, 'name'))
    class Meta:
        model = sm_models.Reservation
        fields = ('id', 'property', 'start_date', 'end_date', 'guest_name', 'guest_email', 'number_of_guests', 'total_price')
        export_order = fields
   
        
    def before_import_row(self, row, **kwargs):
        # Logique personnalisée avant l'import de chaque ligne
        pass

    def after_import_row(self, row, row_result, **kwargs):
        # Logique personnalisée après l'import de chaque ligne
        pass
    

@admin.register(sm_models.Reservation)
class ReservationAdmin(ImportExportModelAdmin):
    resource_class = ReservationResource
    #
    date_hierarchy = 'check_in'
    actions = [duplicate_reservation]  # Ajoutez l'action ici
    ## readonly_fields = ('numero', 'created_at', 'invoice_total')
    
    list_display = ('guest_name', 'property', 'check_in', 'check_out', 'reservation_status', 
                    'platform', 'get_price_per_night', 'total_price')
    list_filter = ('reservation_status', 'platform', 'is_business_trip')
    search_fields = ('guest_name', 'guest_email', 'property__name')
    readonly_fields = ('booking_date', 'created_at', )

    fieldsets = (
        ('Reservation Details', {
            'fields': (
                ('property', 'reservation_status'),
                ('check_in', 'check_out'),
                ('platform', 'is_business_trip'),
            )
        }),
        ('Guest Information', {
            'fields': (
                ('guest_name', 'guest_email'),
                ('guest_phone', 'number_of_guests'),
                'special_requests',
            )
        }),
        ('Financial Details', {
            'fields': (
                ('total_price', 'cleaning_fee', 'service_fee'),
            ),
            'classes': ('collapse',)
        }),
        ('Additional Information', {
            'fields': (
                ('cancellation_policy', 'guest_rating'),
            ),
            'classes': ('collapse',)
        }),
        ('System Information', {
            'fields': (
                ('booking_date', 'created_at'),
                ('created_by', ),
            ),
            'classes': ('collapse',)
        }),
    )
    
    def get_price_per_night(self, obj):
        return obj.property.get_price_for_date(obj.check_in)
    get_price_per_night.short_description = 'Prix par nuit'


    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ('property', 'guest_name', 'guest_email', 'platform', 'total_price')
        return self.readonly_fields

    def total_price_display(self, obj):
        return format_html('<span style="color: green; font-weight: bold;">${}</span>', obj.total_price)
    
    total_price_display.short_description = 'Total Price'

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



@admin.register(sm_models.ServiceTask)
class ServiceTaskAdmin(admin.ModelAdmin):
    list_display = ('get_description', 'get_client', 'get_guestname', 'property', 
                    'start_date', 'end_date', 'status', 'completed')
    list_filter = ('status', 'completed', 'type_service')
    search_fields = ('property__name', 'employee__user__username', 'reservation__guest_name')
    date_hierarchy = 'start_date'
    #readonly_fields = ('created_at', )

    fieldsets = (
        ('Task Details', {
            'fields': (
                'description',
                ('property', 'reservation'),
                ('employee', 'type_service'),
                ('start_date', 'end_date'),
            )
        }),
        ('Status Information', {
            'fields': (
                ('status', 'completed'),
            )
        }),
        ('System Information', {
            'fields': (
                ('created_by',),
            ),
            'classes': ('collapse',)
        }),
    )


    def get_description(self, obj):
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    get_description.short_description = 'Description'

    def get_client(self, obj):
        return obj.property.owner.username if obj.property and obj.property.owner else '-'
    get_client.short_description = 'Client'

    def get_guestname(self, obj):
        return obj.reservation.guest_name if obj.reservation else '-'
    get_guestname.short_description = 'Guest Name'


# Personnalisation de l'admin pour Calendar et Event
class CalendarAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug', )
    search_fields = ('name', 'slug')


class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'start', 'end', 'calendar')
    list_filter = ('start', 'end', 'calendar')
    search_fields = ('title',)

     
    
    
# Réenregistrement des modèles de django-scheduler avec notre configuration personnalisée
admin.site.unregister
admin.register(Event, EventAdmin)


from .models import Incident
from staff.models import Employee
