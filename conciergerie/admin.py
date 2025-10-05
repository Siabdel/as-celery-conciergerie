# Register your models here.

# conciergerie/admin.py
from django.contrib import admin
from .models import (
    Property, Reservation, PricingRule, ServiceTask,
    AdditionalExpense, Incident, CheckoutInventory, PropertyImage
)

from django.shortcuts import render, redirect
from django.urls import path
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from conciergerie.forms import ReservationImportForm
from import_export import resources, fields, widgets
from django.contrib.admin import StackedInline

from conciergerie.csv_import import import_reservations_csv_pandas 
from conciergerie import models as sm_models
from django.db.models import Count, Sum
from django.core.exceptions import ValidationError
from django.utils.html import format_html
from core import models as cr_models
from django.utils.text import slugify
from django.urls import reverse
from django.utils.timezone import now
from core.models import ASBaseTimestampMixin

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

class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 1


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
    
@admin.register(sm_models.AdditionalExpense)
class AdditionalExpenseAdmin(admin.ModelAdmin):
    list_display = ('property', 'expense_type', 'amount', )
    list_filter = ('expense_type', 'property', )
    search_fields = ('property__name', 'description')
 
@admin.register(sm_models.Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'agency', 'owner', 'price_per_night_display', 'address_preview')
    list_filter = ('agency', 'type', 'owner')
    search_fields = ('name', 'address', 'owner__username')
    readonly_fields = ('created_at', 'updated_at', 'created_by')
    inlines = [PricingRuleInline, PropertyImageInline, PropertyIncidentInline, AdditionalExpenseInline]

    fieldsets = (
        ('Property Information', {
            'fields': (
                'name', 'agency',
                ('type', 'owner'),
                'price_per_night',
                'gerant',
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
        # pour owner : ses biens
        # pour employee : biens de son agence
        return qs.for_user(request.user)
    
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


@admin.register(PricingRule)
class PricingRuleAdmin(admin.ModelAdmin):
    list_display = ["property", "start_date", "end_date", "price_per_night", "is_active", "priority"]


@admin.register(ServiceTask)
class ServiceTaskAdmin(admin.ModelAdmin):
    list_display = ["property", "type_service", "start_date", "end_date", "employee", "completed"]
    list_filter = ('agency', 'property', )




@admin.action(description=_("Dupliquer les réservations sélectionnées"))
def duplicate_reservation(modeladmin, request, queryset):
    for reservation in queryset:
        # Créer une nouvelle réservation avec les mêmes données
        try :
            new_reservation = Reservation.objects.create(
                agency = reservation.agency,
                guest_name = reservation.guest_name,
                guest_email = reservation.guest_email,
                guest_phone = reservation.guest_phone,
                number_of_guests = reservation.number_of_guests,
                total_price = reservation.total_price,
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

#-------------------
#- Reservation Admin
#---------------------------------
@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    ## list_display = [f.name for f in Reservation._meta.fields if f.name.endswith('agency')] ['agency']
    list_display = ["agency", "property", "guest_name", "guest_nationality","check_in", 
                    "check_out", "reservation_status",
                    'platform', 'get_price_per_night', 'total_price']
    list_filter = ["agency", "reservation_status", "platform"]
    search_fields = ["guest_name", "guest_email"]

    # vos list_display, list_filter existants
    change_list_template = "admin/conciergerie/reservation/change_list.html"  # surcharge
    resource_class = ReservationResource
    #
    date_hierarchy = 'check_in'
    actions = [duplicate_reservation]  # Ajoutez l'action ici
    ## readonly_fields = ('numero', 'created_at', 'invoice_total')
    
    search_fields = ('guest_name', 'guest_email', 'property__name')
    readonly_fields = ('booking_date', 'created_at', 'agency')

    fieldsets = (
        ('Reservation Details', {
            'fields': (
                ('agency', 'property', 'reservation_status'),
                ('check_in', 'check_out'),
                ('platform', ),
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
    
    # ------------------------------------------------------------------
    def save_model(self, request, obj, form, change):
        if not change:
            if hasattr(request.user, "employee"):      # collaborateur
                obj.agency = request.user.employee.agency
                # owner = propriétaire du bien (inchangé)
                obj.owner = obj.property.owner
            elif request.user.properties_owned.exists():  # owner
                obj.agency = obj.property.agency
                obj.owner = request.user
            else:
                raise PermissionDenied("Vous n’êtes rattaché à aucune agence.")
        super().save_model(request, obj, form, change)
        
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

    # ------------------------------------------------------------------
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # collaborateur : toutes les résas de son agence
        if hasattr(request.user, "employee"):
            return qs.filter(agency=request.user.employee.agency)
        # owner : uniquement ses résas
        return qs.filter(property__owner=request.user)

    # ------------------------------------------------------------------
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "property":
            if hasattr(request.user, "employee"):   # collaborateur
                kwargs["queryset"] = Property.objects.filter(
                    agency=request.user.employee.agency
                )
            elif request.user.properties_owned.exists():  # owner
                kwargs["queryset"] = request.user.properties_owned.all()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

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

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path("import-csv/", self.import_csv, name="reservation_import"),
        ]
        return my_urls + urls

    def import_csv(self, request):
        if request.method == "POST":
            form = ReservationImportForm(request.POST, request.FILES)
            if form.is_valid():
                res = import_reservations_csv_pandas(form.read(), request.user)
                if res["errors"]:
                    for e in res["errors"]:
                        messages.error(request, e)
                messages.success(
                    request,
                    _("Import terminé : %(created)d créée(s), %(updated)d mise(s) à jour") % res
                )
                return redirect("admin:conciergerie_reservation_changelist")
        else:
            form = ReservationImportForm()
        context = dict(
            self.admin_site.each_context(request),
            form=form,
            title=_("Importer des réservations (CSV)")
        )
        return render(request, "admin/csv_import_form.html", context)

admin.site.register(CheckoutInventory)