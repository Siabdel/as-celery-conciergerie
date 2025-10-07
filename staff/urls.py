# conciergerie/urls.py  (ajout en fin de fichier)

from django.contrib import admin
from django.urls import path, include

from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from staff.staff_dashboard_api_views import (
    EmployeeListAPIView,
    AbsenceListAPIView,
    AbsenceUpdateAPIView,
    TaskListAPIView,
    StaffOccupancyKPIView,
    TasksDelayKPIView,
    PendingLeavesKPIView,
    StaffCSATKPIView,
)

from staff import views as rh_views

app_name = "staff"


urlpatterns = [
    path('home/', rh_views.home , name='rh_home'),
]

#-----------------------------
# - API
#-----------------------------
#
urlpatterns += [
    # employees
    path('api/employees/', EmployeeListAPIView.as_view(), name='api-employee-list'),
    # absences
    path('api/absences/', AbsenceListAPIView.as_view(), name='api-absence-list'),
    path('api/absences/<int:pk>/', AbsenceUpdateAPIView.as_view(), name='api-absence-update'),
    # tasks
    path('api/tasks/', TaskListAPIView.as_view(), name='api-task-list'),
    # RH KPIs
    path('api/kpi/staff-occupancy/', StaffOccupancyKPIView.as_view(), name='kpi-staff-occupancy'),
    path('api/kpi/tasks-delay/', TasksDelayKPIView.as_view(), name='kpi-tasks-delay'),
    path('api/kpi/pending-leaves/', PendingLeavesKPIView.as_view(), name='kpi-pending-leaves'),
    path('api/kpi/staff-csat/', StaffCSATKPIView.as_view(), name='kpi-staff-csat'),
]
