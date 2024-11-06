
from django.urls import path
from .pdf_views import generate_pdf_property_report
from .views import (
    PropertyReservationReport,
    EmployeePerformanceReport,
    PlatformReservationReport,
    ServiceTaskReportView,
    ReservationRevenueReportView,
)

""" 
Chaque path() définit une URL pour un rapport spécifique :
-->  reports/property-reservations/ affichera le rapport des réservations par propriété.
--> /reports/employee-performance/ affichera le rapport des performances des employés.
--> /reports/platform-reservations/ affichera le rapport des réservations par plateforme.
--> /reports/property-reservations/pdf/ permettra de télécharger le rapport des réservations par propriété en format PDF.
Pour utiliser ces URLs :
Assurez-vous que ce fichier urls.py est inclus dans le fichier urls.py principal de votre projet Django.
"""

urlpatterns = [
    path('property-reservations/', PropertyReservationReport.as_view(), name='property_reservation_report'),
    path('employee-performance/', EmployeePerformanceReport.as_view(), name='employee_performance_report'),
    path('platform-reservations/', PlatformReservationReport.as_view(), name='platform_reservation_report'),
    ## Report
]

## Report 

urlpatterns += [
    path('property-reservations/pdf/', generate_pdf_property_report, name='property_reservation_pdf'),
    path('service-task/', ServiceTaskReportView.as_view(), name='service_request_report'),
    path('revenue-by-property/', ReservationRevenueReportView.as_view(), name='reservation_revenue_report'),
]