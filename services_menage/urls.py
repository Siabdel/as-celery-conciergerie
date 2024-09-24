
from django.urls import path
from services_menage import views 
from django.http import JsonResponse
from django.shortcuts import render

urlpatterns = [
    # ...
    path('calendar/', lambda request: render(request, 'services_menage/templates/fullcalendar.html'), name='calendar'),
    ## path('api/v1/calendar/employee-tasks/', EmployeeTaskCalendarView.as_view(), name='employee_task_calendar'),
]