from django.urls import path
from .views import RevenueChartView, revenue_data, RevenueReportView, revenue_report_data
from .views import ConciergerieRevenueView
from .api_views import RevenueReportAPIView, TauxOccupationAPIView


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
]
#-------------------------------------------
#--- API's            
#-------------------------------------------

urlpatterns += [
    # taux occupation des proprietes par mois
    path('api/taux-occupation/', TauxOccupationAPIView.as_view(), name='revenue_report_chart'),
    # Revenue Report
    path('api/revenue-report/', RevenueReportAPIView.as_view(), name='revenue_report_api'),
]
#-------------------------------------------