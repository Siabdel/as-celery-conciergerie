
from django.urls import path, include
from django.http import JsonResponse
from django.shortcuts import render
from rest_framework.routers import DefaultRouter
from services_menage import api_views 
from services_menage import views 

app_name = "agence"

router = DefaultRouter()
router.register(r'property', api_views.PropertyViewSet)
router.register(r'employees', api_views.EmployeeViewSet)
router.register(r'reservations', api_views.ReservationViewSet)
router.register(r'maintenance_tasks', api_views.ServiceTaskViewSet)
router.register(r'calendars', api_views.CalendarViewSet)
router.register(r'events', api_views.EventViewSet)
# Formulaire 
router.register(r'checkout-inventory', api_views.CheckoutInventoryViewSet)


urlpatterns = [
    path('', views.home, name='home'),
    path('home/', views.home, name='home'),
    path('dashboard/', views.conciergerie_page, name='dashboard'),
    path('personnel/', views.conciergerie_page, name='employee_list'),
    ##
    path('property/', views.PropretyList.as_view(), name='property_list'),
    path('show/<int:pk>/', views.PropertyDetail.as_view(), name='property_detail'),
    path('resa/', views.conciergerie_page, name='reservations'),
    path('report/', views.reporting_page, name='dashboard_report'),
    path('planning/', views.planning_page, name='planning_page'),
]

#-------------------
# Rest API 
#-------------------

urlpatterns += [
    path('api/', include(router.urls), name='api_router'),
    ## path('api/v1/calendar/employee-tasks/', EmployeeTaskCalendarView.as_view(), name='employee_task_calendar'),
    path('api/tasks/', api_views.get_employee_tasks, name='get_employee_tasks'),
    path('api/event/<int:pk>/update/', api_views.ServiceTaskEventUpdateView.as_view(), name='event-update'),
]
