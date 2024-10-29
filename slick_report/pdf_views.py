""" 
Génération de rapports PDF
Pour générer des rapports PDF, nous allons utiliser la bibliothèque reportlab. 
Voici comment vous pouvez implémenter une fonction pour générer un PDF à partir des données de rapport :
"""

from django.template.loader import render_to_string
from django.utils import timezone
from django.http import HttpResponse
from weasyprint import HTML
from django.conf import settings
import os
from .views import PropertyReservationReport


def generate_pdf_property_report(request):
    # Créez une instance de la vue avec la requête
    report_view = PropertyReservationReport()
    report_view.request = request  # Ajoutez manuellement l'attribut request
    report_view.setup(request)  # Configurez la vue avec la requête
    report_data = report_view.get_context_data()
    #"""Generate PDF Property Report"""
    
    # Obtenez les données du rapport
    context = report_view.get_context_data()
    #report_data = report_view.get_report_data()
    report_data = context.get('report_data', {})
    
    # Préparez le contexte pour le template PDF
    pdf_context = {
        "report_data": report_data,
        "generated_date": timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
        "host": request.get_host(),
    }
    
    # Générez le PDF
    html_string = render_to_string('property_report.html', pdf_context)
    html = HTML(string=html_string, base_url=request.build_absolute_uri())
    pdf_file = html.write_pdf()
     # Create HTTP response with PDF
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="property_report.pdf"'
    
    return response
    

def generate_pdf_property_report__2(request):
    # Créez une instance de la vue avec la requête
    report_view = PropertyReservationReport()
    report_view.request = request  # Ajoutez manuellement l'attribut request
    report_view.setup(request)  # Configurez la vue avec la requête

    # Obtenez les données du rapport
    context = report_view.get_context_data()
    report_data = context['report_data']
    
    # Préparez le contexte pour le template PDF
    pdf_context = {
        "report_data": report_data,
        "generated_date": timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
        "host": request.get_host(),
    }
    
    # Générez le PDF
    html_string = render_to_string('pdf/property-report.html', pdf_context)
    html = HTML(string=html_string, base_url=request.build_absolute_uri())
    pdf_file = html.write_pdf()
    
    # Créez la réponse HTTP avec le PDF
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="property_report.pdf"'
    
    return response

