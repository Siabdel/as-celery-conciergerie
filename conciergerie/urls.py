

from django.contrib import admin
from django.urls import path, include

from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

# --- Import de vos ViewSets ---
from conciergerie.api_views import (
    PropertyViewSet, ReservationViewSet, ServiceTaskViewSet,
    IncidentViewSet, AdditionalExpenseViewSet, EmployeeViewSet
)
from conciergerie.reporting_views import (
    RevenueReportView, PropertyRevenueMonthlyView,
    OccupancyRateView, FinancialPDFReportView
)

# --- Pour les utilisateurs ---
from django.contrib.auth import get_user_model
from rest_framework import viewsets, serializers
## webhooks OTA
from conciergerie.api_views_period import ReservationPeriodAPIView, ServiceTaskPeriodAPIView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from conciergerie.reporting_views import (
    RevenueReportPDFView,
    PropertyRevenueMonthlyPDFView,
    OccupancyRatePDFView,
)
from conciergerie.ota_views import airbnb_webhook, booking_webhook
from conciergerie import views as co_views
from conciergerie import api_views_dashboard as co_api_dashboard
from conciergerie import api_views as co_api_views
# api_reporting_views
from conciergerie import api_reporting_views as api_report

app_name = "conciergerie"

# Serializer simple pour User
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ["id", "username", "email", "first_name", "last_name"]

# ViewSet User
class UserViewSet(viewsets.ModelViewSet):
    queryset = get_user_model().objects.all()
    serializer_class = UserSerializer


# --- Router DRF ---
router = DefaultRouter()
router.register(r'properties', PropertyViewSet, basename="property")
router.register(r'reservations', ReservationViewSet, basename="reservation")
router.register(r'tasks', ServiceTaskViewSet, basename="task")
router.register(r'incidents', IncidentViewSet, basename="incident")
router.register(r'expenses', AdditionalExpenseViewSet, basename="expense")
router.register(r'employees', EmployeeViewSet, basename="employee")
router.register(r'users', UserViewSet, basename="user")

# --- URL patterns ---
urlpatterns = [
    
    path("home/", co_views.home, name="home_page"),
    path("", co_views.conciergerie_page , name="home"),
    path('property/', co_views.PropretyList.as_view(), name='property_list'),
    path('show/<int:pk>/', co_views.PropertyDetail.as_view(), name='property_detail'),
    path('resa/<int:reservation_id>/show/', co_views.details_reservation, name='checkin_detail'),
    path('resa/<int:resa>/show/', co_views.details_reservation, name='checkin_detail'),
    path('property/<int:property_id>/show/', co_views.property_details_plus, name='property_details_plus'),
    ## reprt 
    path('property/<int:property_id>/report/', co_views.property_report, name='property_report'),

    # API métiers
    path("api/", include(router.urls)),

    # api properties
    path("api/properties/myagency/", PropertyViewSet.as_view({'get': 'mine'}), name="property-my_agency"),

    # Auth JWT
    path("api/auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # Reporting
    path("api/reports/revenue/", RevenueReportView.as_view(), name="revenue-report"),
    path("api/reports/property/<int:property_id>/monthly-revenue/", PropertyRevenueMonthlyView.as_view(),
         name="property-monthly-revenue"),
    path("api/reports/property/<int:property_id>/occupancy/", OccupancyRateView.as_view(), name="occupancy-rate"),
    path("api/reports/pdf/", FinancialPDFReportView.as_view(), name="financial-pdf"),
]

## generer rapport pdf 

urlpatterns += [
    path("api/reports/revenue/pdf", RevenueReportPDFView.as_view(), name="revenue-report-pdf"),
    path("api/reports/property/<int:property_id>/monthly-revenue/pdf",
         PropertyRevenueMonthlyPDFView.as_view(), name="property-monthly-revenue-pdf"),
    path("api/reports/property/<int:property_id>/occupancy/pdf",
         OccupancyRatePDFView.as_view(), name="occupancy-rate-pdf"),
]

# conciergerie/ota_webhooks/urls.py

urlpatterns += [
    path("webhooks/airbnb/", airbnb_webhook, name="airbnb-webhook"),
    path("webhooks/booking/", booking_webhook, name="booking-webhook"),
]

# --- Documentation OpenAPI avec drf-spectacular ---

urlpatterns += [
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]


urlpatterns += [
    # endpoints périodiques
    # conciergerie/urls.py
    path("api/today-checkins/", api_report.TodayCheckinsView.as_view(), name="today-checkins"),
    path("reservations/period/<str:period>/", ReservationPeriodAPIView.as_view(), name="resa-period"),
    path("tasks/period/<str:period>/", ServiceTaskPeriodAPIView.as_view(), name="task-period"),
]

##  endpoint pour les taches et reservations par periode
urlpatterns += [
    path("api/dashboard/", co_api_dashboard.DashboardWeekAPIView.as_view(), name="api-dashboard"),
    # conciergerie/urls.py
    path("api/dashboard/week/", co_api_dashboard.DashboardWeekAPIView.as_view(), name="api-dashboard-week"),
    path("api/dashboard/month/", co_api_dashboard.DashboardMonthAPIView.as_view(), name="api-dashboard-month"),
    path("api/dashboard/quarter/", co_api_dashboard.DashboardQuarterAPIView.as_view(), name="api-dashboard-quarter"),
    path("api/dashboard/year/", co_api_dashboard.DashboardYearAPIView.as_view(), name="api-dashboard-year"),
]

## 

## some report api's 
# indicateurs cles 
urlpatterns += [
    # --- indicateurs clés ---
    path("api/kpi/available/", api_report.AvailableApartmentsAPIView.as_view(), name="kpi-available"),
    path("api/kpi/vacancy/", api_report.VacancyRateAPIView.as_view(), name="kpi-vacancy"),
    path("api/kpi/occupancy/", api_report.OccupancyRateAPIView.as_view(), name="kpi-occupancy"),
    path("api/kpi/active-bookings/", api_report.ActiveBookingsAPIView.as_view(), name="kpi-active"),
    path("api/kpi/revpar/", api_report.RevPARAPIView.as_view(), name="kpi-revpar"),
    path("api/kpi/avg-basket/", api_report.AvgBasketAPIView.as_view(), name="kpi-avg-basket"),
    path("api/kpi/gross-margin/", api_report.GrossMarginAPIView.as_view(), name="kpi-margin"),
    path("api/kpi/loyalty/", api_report.LoyaltyRateAPIView.as_view(), name="kpi-loyalty"),
    path("api/kpi/csat/", api_report.CSATAPIView.as_view(), name="kpi-csat"),
    path("api/kpi/avg-service-cost/", api_report.AvgServiceCostAPIView.as_view(), name="kpi-avg-cost"),
    path("api/kpi/portfolio-size/", api_report.PortfolioSizeAPIView.as_view(), name="kpi-portfolio"),
    path("api/kpi/avg-stay-duration/", api_report.AvgStayDurationAPIView.as_view(), name="kpi-avg-stay"),
    path("api/kpi/acceptance/", api_report.AcceptanceRateAPIView.as_view(), name="kpi-acceptance"),
    path("api/kpi/clv/", api_report.CLVAPIView.as_view(), name="kpi-clv"),
    path("api/kpi/cac/", api_report.CACAPIView.as_view(), name="kpi-cac"),
]


# --------------  DETAIL SUPPLY  -----------------
# single property full payload
urlpatterns += [
    path("apiplus/properties/<int:pk>/", co_api_views.PropertyDetailAPIView.as_view(),
     name="property-detail"),

    # reservations linked to ONE property (calendar & check-ins)
    path("api/reservations/property/<int:property_id>/",
        co_api_views.ReservationByPropertyListAPIView.as_view(),
        name="resa-by-property"),

    # revenue & occupancy dedicated to ONE property
    path("api/reports/property/<int:property_id>/revenue/",
        co_api_views.PropertyRevenueAPIView.as_view(),
        name="property-revenue"),

    path("api/reports/property/<int:property_id>/occupancy/",
        co_api_views.PropertyOccupancyAPIView.as_view(),
        name="property-occupancy"),
]

from conciergerie import api_property_public_views as api_appart

# --------------  DETAIL SUPPLY  -----------------
# single property full payload
#------------------------------------------------
