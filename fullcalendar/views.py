import requests
from django.shortcuts import render
from django.views.generic import ListView, CreateView, DetailView
from django.views.generic import TemplateView
from services_menage.models import Property

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

## Calendier des reservations par property
class FullcalendarPropertyView(TemplateView):
    template_name = 'fullcalendar_property_resa.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        property_id = context["property_id"]
        property = Property.objects.get(pk=property_id)
        context["property"] = property
        return context


def test_api(url):
    # L'URL de base de votre API
    if not url :
        base_url = "http://localhost:8000/pandas"

    # L'ID de la propriété dont vous voulez obtenir les réservations
    property_id = 10

    # Construire l'URL complète avec le paramètre de requête
    url = f"{base_url}/reservations/?property_id={property_id}"

    # Faire la requête GET
    response = requests.get(url)

    # Vérifier si la requête a réussi
    if response.status_code == 200:
        # La requête a réussi, vous pouvez accéder aux données
        reservations = response.json()
        print(f"Réservations pour la propriété {property_id}:")
        for reservation in reservations:
            print(f"ID: {reservation['id']}, Date de début: {reservation['start_date']}, Date de fin: {reservation['end_date']}")
    else:
        # La requête a échoué
        print(f"Erreur lors de la récupération des réservations: {response.status_code}")
        print(response.text)
