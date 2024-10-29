""" 
Génération de rapports PDF
Pour générer des rapports PDF, nous allons utiliser la bibliothèque reportlab. 
Voici comment vous pouvez implémenter une fonction pour générer un PDF à partir des données de rapport :
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
from slick_report.views import PropertyReservationReport, PlatformReservationReport
from django.http import HttpResponse
from .views import PropertyReservationReport

def generate_pdf_report(report_data, title):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []

    # Ajout du titre
    styles = getSampleStyleSheet()
    elements.append(Paragraph(title, styles['Heading1']))

    # Création du tableau
    data = [report_data['columns']]  # En-têtes
    for row in report_data['data']:
        data.append([str(item) for item in row])

    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 12),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))

    elements.append(table)
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf

# Utilisation dans une vue

def download_pdf_report(request):
    report_view = PropertyReservationReport()
    report_data = report_view.get_report_data()
    
    # Fonction helper pour obtenir le nom de la colonne
    def get_column_name(col):
        if isinstance(col, dict):
            return col.get('verbose_name', col.get('name', ''))
        return str(col)
    
    # Fonction helper pour obtenir la valeur d'une cellule
    def get_cell_value(row, col):
        if isinstance(row, dict):
            return row.get(get_column_name(col), '')
        elif isinstance(row, (list, tuple)):
            try:
                index = next(i for i, c in enumerate(report_view.columns) if get_column_name(c) == get_column_name(col))
                return row[index]
            except StopIteration:
                return ''
        return ''
    
    # Convertir les données du rapport en un format adapté pour le PDF
    pdf_data = {
        'columns': [get_column_name(col) for col in report_view.columns],
        'data': [[get_cell_value(row, col) for col in report_view.columns] for row in report_data['data']]
    }
    
    pdf = generate_pdf_report(pdf_data, "Rapport des réservations par propriété")
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="property_reservation_report.pdf"'
    response.write(pdf)
    return response