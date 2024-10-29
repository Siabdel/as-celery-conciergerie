from django.urls import path
from .views import RevenueChartView, revenue_data, RevenueReportView, revenue_report_data

urlpatterns = [
    path('revenue-chart/', RevenueChartView.as_view(), name='revenue_chart'),
    path('revenue-data/', revenue_data, name='revenue_data'),
    #
     # ... vos autres URLs ...
    path('revenue-report/', RevenueReportView.as_view(), name='revenue_report'),
    path('revenue-report-data/', revenue_report_data, name='revenue_report_data'),
]