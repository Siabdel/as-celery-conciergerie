
from django.urls import path, include
from django.http import JsonResponse
from django.shortcuts import render
from rest_framework.routers import DefaultRouter
from services_menage import api_views 
from services_menage import views 

app_name = "agence"

router = DefaultRouter()
## Api reservations par Property
router.register(r'property', api_views.PropertyViewSet)
router.register(r'reservations', api_views.ReservationViewSet)
router.register(r'employees', api_views.EmployeeViewSet)
router.register(r'maintenance_tasks', api_views.ServiceTaskViewSet)
router.register(r'calendars', api_views.CalendarViewSet)
router.register(r'events', api_views.EventViewSet)
#router.register(r'additional-expenses', api_views.AdditionalExpenseViewSet)
# additional-expenses by property
router.register(r'property-depenses', api_views.PropertyAdditionalDepenseExpenseViewSet) 
# Formulaire 
router.register(r'checkout-inventory', api_views.CheckoutInventoryViewSet)

##-----------------------------------
## Api Comptabilité
"""
router.register(r'checkin-inventory', api_views.CheckinInventoryViewSet)
router.register(r'inventory-items', api_views.InventoryItemViewSet)
router.register(r'inventories', api_views.InventoryViewSet)
router.register(r'clients', api_views.ClientViewSet)
router.register(r'revenue-statements', api_views.RevenueStatementViewSet)
router.register(r'revenue-statement-items', api_views.RevenueStatementItemViewSet)
router.register(r'invoices', api_views.InvoiceViewSet)
router.register(r'invoice-items', api_views.InvoiceItemViewSet)
router.register(r'payments', api_views.PaymentViewSet)
router.register(r'payment-modes', api_views.PaymentModeViewSet)
router.register(r'property-expenses', api_views.PropertyExpenseViewSet)
router.register(r'property-expense-categories', api_views.PropertyExpenseCategoryViewSet)
router.register(r'property-expense-items', api_views.PropertyExpenseItemViewSet)
router.register(r'vendors', api_views.VendorViewSet)
router.register(r'purchase-orders', api_views.PurchaseOrderViewSet)
router.register(r'purchase-order-items', api_views.PurchaseOrderItemViewSet)
router.register(r'business-expenses', api_views.BusinessExpenseViewSet)
router.register(r'business-expense-categories', api_views.BusinessExpenseCategoryViewSet)
router.register(r'business-expense-items', api_views.BusinessExpenseItemViewSet)
router.register(r'business-expense-vendors', api_views.VendorViewSet) 
"""


#-------------------
# Rest API 
#-------------------

urlpatterns = [
    path('api/', include(router.urls), name='api_router'),
    ## path('api/v1/calendar/employee-tasks/', EmployeeTaskCalendarView.as_view(), name='employee_task_calendar'),
    path('api/tasks/', api_views.get_employee_tasks, name='get_employee_tasks'),
    path('api/event/<int:pk>/update/', api_views.ServiceTaskEventUpdateView.as_view(), name='event-update'),
    path('api/releve/', api_views.calculate_revenue_statement, name='api_releve_revenue'),
]


urlpatterns += [
    path('home/', views.home, name='home'),
    path('', views.conciergerie_page, name='dashboard'),
    path('dashboard/', views.conciergerie_page, name='dashboard_home'),
    path('personnel/', views.conciergerie_page, name='employee_list'),
    ##
    path('property/', views.PropretyList.as_view(), name='property_list'),
    path('show/<int:pk>/', views.PropertyDetail.as_view(), name='property_detail'),
    path('resa/', views.conciergerie_page, name='reservations'),
    path('report/', views.reporting_page, name='dashboard_report'),
    path('planning/', views.planning_page, name='planning_page'),
]

