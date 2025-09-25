from django.urls import path, include
from .views import RevenueChartView, revenue_data, RevenueReportView, revenue_report_data
from .views import ConciergerieRevenueView, PropertyRevenueView
from .api_views import RevenueReportAPIView, TauxOccupationAPIView, property_revenue_by_month
from pandas_report import api_views 
from pandas_report.pdf_views import generate_pdf_property_report
from rest_framework.routers import DefaultRouter

app_name = "pandas_report"


urlpatterns = [
    path('revenue-chart/', RevenueChartView.as_view(), name='revenue_chart'),
    path('revenue-data/', revenue_data, name='revenue_data'), ## API json
    #
     # ... vos autres URLs ...
    path('revenue-report-data/', revenue_report_data, name='revenue_report_data'),
]

#-------------------------------------------
#--- Revenue Vue.js
#-------------------------------------------
urlpatterns += [
    # ... vos autres URLs ...
    # reporting views 
    path('revenue/', ConciergerieRevenueView.as_view(), name='revenue_report'),
    # revenue report with charts
    path('revenue-report/', RevenueReportView.as_view(), name='revenue_report_chart'),
    # property revenue report by property_id
    path('property-revenue-report/<int:property_id>', PropertyRevenueView.as_view(), name='property_revenue_report'),
    # property revenue per month API
    # pdf report 
    path('pdf-report/', generate_pdf_property_report,name='pdf_property_report'),
    
]
#-------------------------------------------
#--- API's            
#-------------------------------------------

urlpatterns += [

    path('api/reservations/', api_views.ReservationViewSet.as_view({'get', 'list'}), name='api-reservations-by-property'),
    # taux occupation des proprietes par mois
    path('api/taux-occupation/', TauxOccupationAPIView.as_view(), name='api_revenue_report_chart'),
    # Revenue Report
    path('api/revenue-report/', RevenueReportAPIView.as_view(), name='api_revenue_report'),
    # property revenue per month
    path('api/property/<int:property_id>/revenue/', api_views.property_revenue_by_month, name='api_property_revenue_by_month'),
    path('api/property/<int:property_id>/occupancy/', api_views.property_occupancy_rate_by_month, name='api_property_occupancy_rate_by_month'),  
    ## Evolution des prix par property
    path('api/property/<int:property_id>/price-evolution/', api_views.get_monthly_price_evolution_by_property, name='api_property_price_evolution'),

]
#-------------------------------------------