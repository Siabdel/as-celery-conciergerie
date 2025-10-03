from django.shortcuts import render
from datetime import datetime
from django.http import HttpResponse
import pandas as pd


# conciergerie/ota_webhooks/views.py
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from conciergerie.models import Property, Reservation
from conciergerie.serializers import ReservationSerializer
from conciergerie.serializers import AirbnbWebhookSerializer, BookingWebhookSerializer
from conciergerie.ota_webhooks.signatures import verify_airbnb, verify_booking
from django.conf import settings
import logging
from collections import defaultdict
from django.views.generic import ListView, CreateView, DetailView
from conciergerie import models as co_models

logger = logging.getLogger(__name__)

def home(request):
    return render(request, "conciergerie/dashboard_conciergeriepro.html", {})

def conciergerie_page(request):
    return render(request, "dashboard_page.html")

class PropretyList(ListView):
    
    template_name = "property_list.html"
    context_object_name = "properties"
    paginate_by = 10

    def get_queryset(self):
        if self.request.user.is_authenticated:
            properties = co_models.Property.objects.all().order_by( "-created_at")
            return properties
        else:
            return co_models.Property.objects.none()

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get the data
        context = super(PropretyList, self).get_context_data(**kwargs)
        try:
            recent_properties = context["properties"][:4]
        except (IndexError, AttributeError):
            recent_properties = None
        context["recent_properties"] = recent_properties
        return context


class PropertyDetail(DetailView):
    template_name = "property_revenue_vue.html"
    #template_name = "property_list.html"
    model = co_models.Property
    context_object_name = "property"
   
    def get_context_data(self, **kwargs):
        context =  super().get_context_data(**kwargs)
        # Récupérer les images associées à ce produit en utilisant la méthode que nous avons définie dans le modèle

        data = {}
        aujourdhui = datetime.now()
        nb_reservations = 0
        property  = self.get_object()
        reservations = \
            co_models.Reservation.objects.filter(property__id=property.id, 
                                                 reservation_status__in=['CONFIRMED', 'COMPLETED', 'PENDING']).order_by("-check_in")
        #
        for resa in reservations :
            nb = len(pd.date_range(resa.check_in, resa.check_out))    
            nb_reservations += len(pd.date_range(resa.check_in, resa.check_out))    
            ##print(f"resa ckeckin : {resa.check_in} nb_reservation : {nb}" )
        
        nb_reservations = len(reservations)
        context.update( {'property' : self.get_object()})
        context.update( { 'property_images' : property.get_images()})

        ## nb reservations 
        last_year = datetime(aujourdhui.year - 1, aujourdhui.month, aujourdhui.day)
        context.update( { 'nb_reservations_last_year' : 
            len(reservations.filter(check_in__year = last_year.year))})

        #raise Exception(len(reservations.filter(check_out__year = last_year.year)))

        context.update( { 'nb_reservations_now' : len(reservations.filter(check_in__year = aujourdhui.year))})
        
        next_year = datetime(aujourdhui.year + 1, aujourdhui.month, aujourdhui.day)
        context.update( { 'nb_reservations_next_year' : len(reservations.filter(check_in__year = next_year.year))})
        ## dernier client 
        last_resa = reservations.last()
        context.update( { 'last_resa' : last_resa})
        context.update( { 'annees' : [last_year.year, aujourdhui.year, next_year.year  ]})
        ## dernier Incident
        incidents_enours = co_models.Incident.objects.filter(property__id=property.id, status='EN_COURS') 
        context.update( { 'last_incidents' : incidents_enours})
        
        #raise Exception("images : ", property_images)
        return context
    
## CustomCalendar reservations
def calendar_reservation(request):
    return render(request, 'fullcalendar_resa.html')

## CustomCalendar reservations
def calendar_employee(request):
    return render(request, 'fullcalendar_emp.html')