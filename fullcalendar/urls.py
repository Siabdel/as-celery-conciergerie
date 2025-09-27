from django.urls import path, include
from django.http import JsonResponse
from django.shortcuts import render
from rest_framework.routers import DefaultRouter
from fullcalendar import views 

app_name = "fullcalendar"


urlpatterns = [
    path('home/', views.home, name='calendar_home'),
    path('resa/', views.calendar_reservation, name='calendar_resa'),
    path('empl/', views.calendar_employee, name='calendar_empl'),
    ## path('api/v1/calendar/employee-tasks/', EmployeeTaskCalendarView.as_view(), name='employee_task_calendar'),
    ##
    path('cal/property/<int:property_id>', views.FullcalendarPropertyView.as_view(), name='calendar_property_resa'),
]