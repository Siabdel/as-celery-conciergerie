

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
from conciergerie import api_views_dashboard as co_api_views

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
    path('resa/', co_views.conciergerie_page, name='reservations'),
    path('property/', co_views.PropretyList.as_view(), name='property_list'),
    path('show/<int:pk>/', co_views.PropertyDetail.as_view(), name='property_detail'),

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
    path("reservations/period/<str:period>/", ReservationPeriodAPIView.as_view(), name="resa-period"),
    path("tasks/period/<str:period>/", ServiceTaskPeriodAPIView.as_view(), name="task-period"),
]

##  endpoint pour les taches et reservations par periode
urlpatterns += [
    path("api/dashboard/", co_api_views.DashboardWeekAPIView.as_view(), name="api-dashboard"),
    # conciergerie/urls.py
    path("api/dashboard/week/", co_api_views.DashboardWeekAPIView.as_view(), name="api-dashboard-week"),
    path("api/dashboard/month/", co_api_views.DashboardMonthAPIView.as_view(), name="api-dashboard-month"),
    path("api/dashboard/quarter/", co_api_views.DashboardQuarterAPIView.as_view(), name="api-dashboard-quarter"),
    path("api/dashboard/year/", co_api_views.DashboardYearAPIView.as_view(), name="api-dashboard-year"),
]