
from django.urls import path, include
from services_menage import views 
from django.http import JsonResponse
from django.shortcuts import render
from rest_framework.routers import DefaultRouter
from . import api_views 

router = DefaultRouter()
router.register(r'employees', api_views.EmployeeViewSet)
router.register(r'reservations', api_views.ReservationViewSet)
router.register(r'maintenance_tasks', api_views.ServiceTaskViewSet)
router.register(r'calendars', api_views.CalendarViewSet)
router.register(r'events', api_views.EventViewSet)


urlpatterns = [
    path('api/', include(router.urls)),
    path('calendar/', views.calendar_home, name='calendar'),
    ## path('api/v1/calendar/employee-tasks/', EmployeeTaskCalendarView.as_view(), name='employee_task_calendar'),
]