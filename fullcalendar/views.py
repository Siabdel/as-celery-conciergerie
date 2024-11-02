from django.shortcuts import render

# Create your views here.

## home
def home(request):
    return render(request, 'planning_page.html')
## CustomCalendar reservations
def calendar_reservation(request):
    return render(request, 'fullcalendar_resa.html')

## CustomCalendar reservations
def calendar_employee(request):
    return render(request, 'fullcalendar_emp.html')
