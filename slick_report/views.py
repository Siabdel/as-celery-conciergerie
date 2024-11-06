from django.shortcuts import render
from django.db.models import Count, Sum
from slick_reporting.views import ReportView, Chart, SlickReportView
from slick_reporting.fields import ComputationField, SlickReportField
from django.db.models import ExpressionWrapper, DecimalField
from django.db.models import Count, Sum, F
from slick_reporting.generator import ReportGenerator
from django.utils import timezone

from services_menage.models import Reservation, Property, ServiceTask
from staff.models import Employee

# 1. Rapport des réservations par propriété

class PropertyReservationReport(ReportView):
    report_model = Reservation
    date_field = 'check_in'
    group_by = 'property'
    columns = [
        'name',
        ComputationField.create(
            method=Count,
            field='id',
            name='total_reservations',
            verbose_name='Total Réservations'
        ),
        ComputationField.create(
            method=Sum,
            field='total_price',
            name='total_revenue',
            verbose_name='Revenu Total'
        ),
    ]

    # Si vous avez besoin de personnaliser les données du rapport,
    # vous pouvez surcharger la méthode get_context_data au lieu de get_report_data
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Les données du rapport sont déjà incluses dans le contexte par défaut
        # Vous pouvez les modifier ou ajouter d'autres données si nécessaire
        context['generated_date'] = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Si vous voulez accéder aux données du rapport spécifiquement :
        report_data = context.get('report_data', {})
        
        # Vous pouvez ajouter des calculs supplémentaires ou des transformations ici
        # Par exemple, calculer le total global des réservations et des revenus
        total_reservations = sum(item['total_reservations'] for item in report_data)
        total_revenue = sum(item['total_revenue'] for item in report_data)
        
        context['total_reservations'] = total_reservations
        context['total_revenue'] = total_revenue
        
        return context
     

## 2. Rapport des performances des employés
from staff.models import Employee

class EmployeePerformanceReport(ReportView):
    report_model = Reservation
    date_field = 'check_in'
    group_by = 'property__owner'
    columns = [
        'property__owner__username',
        ComputationField.create(
            method=Count,
            field='id',
            name='total_reservations',
            verbose_name='Réservations gérées'
        ),
        ComputationField.create(
            method=Sum,
            field='total_price',
            name='total_revenue',
            verbose_name='Revenu généré'
        ),
    ]
    chart_settings = [
        {
            'type': 'bar',
            'data_source': ['total_reservations'],
            'title_source': ['property__owner__username'],
            'title': 'Nombre de réservations par employé'
        },
    ]

    def get_queryset(self):
        return super().get_queryset().select_related('property__owner')
    
# 3. Rapport des réservations par plateforme

class PlatformReservationReport(ReportView):
    report_model = Reservation
    date_field = 'check_in'
    group_by = 'platform'
    columns = [
        'platform',
        ComputationField.create(
            method=Count,
            field='id',
            name='total_reservations',
            verbose_name='Nombre de réservations'
        ),
        ComputationField.create(
            method=Sum,
            field='total_price',
            name='total_revenue',
            verbose_name='Revenu total'
        ),
    ]
    chart_settings = [
        {
            'type': 'bar',
            'data_source': ['total_reservations', 'total_revenue'],
            'title_source': ['platform'],
            'title': 'Réservations et revenus par plateforme'
        },
    ]

    
class ServiceTaskReportView(ReportView):
    report_model = ServiceTask
    date_field = 'start__date'  # Champ de date à utiliser pour les filtres temporels
    group_by = 'type_service'  # Grouper par type de service
    columns = [
        'type_service',  # Afficher le nom du type de service
        'status',              # Afficher le statut de la demande
        'property',      # Nom du résident
    ]

     

class ReservationRevenueReportView(ReportView): 
    report_model = Reservation
    date_field = 'check_in'
    group_by = 'property__owner'
    columns = [
        'property__name',
        ComputationField.create(
            method=Count,
            field='id',
            name='total_reservations',
            verbose_name='Réservations gérées'
        ),
        ComputationField.create(
            method=Sum,
            field='total_price',
            name='total_revenue',
            verbose_name='Revenu généré'
        ),
        
    ]
    
    # Si vous avez besoin d'un champ calculé pour le revenu moyen
    @classmethod
    def get_custom_fields(cls):
        return [
            ComputationField.create(
                method=lambda qs: Sum('total_price') / Count('id'),
                name='average_revenue',
                verbose_name='Revenu moyen par réservation'
            ),
        ]

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.annotate(
            total_revenue=Sum('total_price'),
            total_reservations=Count('id'),
            average_revenue=ExpressionWrapper(
                Sum('total_price') / Count('id'),
                output_field=DecimalField()
            )
        )

    # Si vous voulez ajouter un champ calculé personnalisé, vous pouvez le faire comme ceci :
    @classmethod
    def get_custom_fields(cls):
        return [
            SlickReportField.create(
                name='average_revenue_per_reservation',
                verbose_name='Revenu moyen par réservation',
                calculation=lambda qs: qs.annotate(
                    avg_revenue=Sum('total_price') / Sum('id')
                ).values('avg_revenue')[0]['avg_revenue'] or 0,
            ),
        ]

    chart_settings = [
        {
            'type': 'bar',
            'data_source': ['total_revenue'],
            'title_source': ['property__name'],
            'title': 'Nombre de réservations par employé'
        },
    ]
