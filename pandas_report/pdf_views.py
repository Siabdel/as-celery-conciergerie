""" 
Génération de rapports PDF
Pour générer des rapports PDF, nous allons utiliser la bibliothèque reportlab. 
Voici comment vous pouvez implémenter une fonction pour générer un PDF à partir des données de rapport :
"""

import os
from io import BytesIO
import requests
from django.template.loader import render_to_string
from django.utils import timezone
from django.http import HttpResponse
from weasyprint import HTML
from django.conf import settings
from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet



def request_url(url_in):  
    """ 
    """
    base_url = settings.BASE_URL  # Par exemple, "http://localhost:8000" ou "https://votredomaine.com"
        
    if url_in :
        url = f"{base_url}{url_in}"
        url = os.path.join(base_url, url_in)
    else :
        url = f"{base_url}/service/api/releve"
        url = os.path.join(base_url, "service/api/releve")
        
    full_url = f"{url}?property_id=10"
    response = requests.get(full_url)
    dataset = response.json()
    return dataset


def generate_pdf_property_report__(request):
    # Créez une instance de la vue avec la requêtefrom django.conf import settings
    # Assurez-vous d'avoir défini BASE_URL dans vos paramètres Django
    
    dataset = request_url("service/api/releve")
    
    ## raise Exception("dataset = ", dataset)
    
    
    # Préparez le contexte pour le template PDF
    pdf_context = {
        "report_data": dataset,
        "generated_date": timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
        "host": request.get_host(),
    }
    
    # Générez le PDF
    html_string = render_to_string('pdf/property_report.html', pdf_context)
    html = HTML(string=html_string, base_url=request.build_absolute_uri())
    pdf_file = html.write_pdf()
     # Create HTTP response with PDF
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="property_report.pdf"'
    
    return response
    


def generate_pdf_property_report2(request):
    # Obtenez les données à partir de l'API
    dataset = request_url("service/api/releve")
    reservations = dataset.get('reservations', [])

    # Créez un buffer pour le PDF
    buffer = BytesIO()

    # Créez le document PDF en mode paysage
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))

    # Créez les éléments du PDF
    elements = []

    # Ajoutez un titre
    styles = getSampleStyleSheet()
    elements.append(Paragraph("Rapport des réservations", styles['Title']))

    # Créez le tableau
    if reservations:
        # Utilisez les clés de la première réservation comme en-têtes
        headers = list(reservations[0].keys())
        data = [headers]  # En-têtes du tableau

        # Ajoutez les données des réservations
        for reservation in reservations:
            data.append([str(reservation.get(key, '')) for key in headers])

        table = Table(data)

        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        elements.append(table)
    else:
        elements.append(Paragraph("Aucune réservation trouvée", styles['Normal']))

    # Construisez le PDF
    doc.build(elements)

    # Préparez la réponse
    buffer.seek(0)
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="property_report.pdf"'

    return response
from io import BytesIO
from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

def generate_pdf_property_report(request):
    # Obtenez les données à partir de l'API
    try:
        dataset = request_url("service/api/releve")
        reservations = dataset.get('reservations', [])
    except Exception as e:
        return HttpResponse(f"Erreur lors de la récupération des données : {e}", status=500)

    # Créez un buffer pour le PDF
    buffer = BytesIO()

    # Définir le document PDF en mode paysage
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),  # Orientation paysage
        rightMargin=30, leftMargin=30,
        topMargin=30, bottomMargin=30
    )

    # Créez les éléments du PDF
    elements = []

    # Ajoutez un titre
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    title_style.textColor = colors.HexColor("#333333")  # Gris foncé
    elements.append(Paragraph("Rapport des réservations (Paysage)", title_style))
    elements.append(Spacer(1, 20))  # Espacement après le titre

    # Créez le tableau
    if reservations:
        # Utilisez les clés de la première réservation comme en-têtes
        headers = list(reservations[0].keys())
        data = [headers]  # En-têtes du tableau

        # Ajoutez les données des réservations
        for reservation in reservations:
            data.append([str(reservation.get(key, '')) for key in headers])

        # Créez le tableau avec des colonnes adaptées
        table = Table(data, colWidths=[doc.width / len(headers)] * len(headers))

        # Appliquer un style de tableau propre
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#f8f9fa")),  # Couleur de l'en-tête
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor("#343a40")),  # Texte de l'en-tête
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#ffffff")),  # Couleur des lignes
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor("#f1f3f5"), colors.HexColor("#ffffff")]),  # Alternance des couleurs
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor("#495057")),  # Couleur du texte
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#dee2e6"))  # Grille
        ]))

        elements.append(table)
    else:
        # Si aucune réservation n'est trouvée
        elements.append(Paragraph("Aucune réservation trouvée.", styles['Normal']))

    # Construisez le PDF
    doc.build(elements)

    # Préparez la réponse
    buffer.seek(0)
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="property_report_landscape.pdf"'

    return response



