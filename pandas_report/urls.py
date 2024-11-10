from django.urls import path
from .views import RevenueChartView, revenue_data, RevenueReportView, revenue_report_data
from .views import ConciergerieRevenueView, PropertyRevenueView
from .api_views import RevenueReportAPIView, TauxOccupationAPIView, property_revenue_by_month
from pandas_report import api_views 


app_name = "report"

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
    path('revenue/', ConciergerieRevenueView.as_view(), name='revenue_report'),
    path('revenue-report/', RevenueReportView.as_view(), name='revenue_report_chart'),
    path('property-revenue-report/<int:property_id>', PropertyRevenueView.as_view(), name='property_revenue_report'),
]
#-------------------------------------------
#--- API's            
#-------------------------------------------

urlpatterns += [
    # taux occupation des proprietes par mois
    path('api/taux-occupation/', TauxOccupationAPIView.as_view(), name='api_revenue_report_chart'),
    # Revenue Report
    path('api/revenue-report/', RevenueReportAPIView.as_view(), name='api_revenue_report_api'),
    # property revenue per month
    path('api/property/<int:property_id>/revenue/', api_views.property_revenue_by_month, name='api_property_revenue_by_month'),
    path('api/property/<int:property_id>/occupancy/', api_views.property_occupancy_rate_by_month, name='property_occupancy_rate_by_month'),  

]
#-------------------------------------------