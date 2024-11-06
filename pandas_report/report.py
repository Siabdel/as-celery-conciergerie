from django.shortcuts import render
import pandas as pd
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from services_menage.models import Reservation, Property

# Create your views here.


def generate_revenue_report():
    """
    # Générer le rapport
    revenue_report = generate_revenue_report()

    # Afficher le rapport
    print(revenue_report)

    # Exporter le rapport en CSV
    revenue_report.to_csv('revenue_report.csv')

    # Exporter le rapport en Excel
    revenue_report.to_excel('revenue_report.xlsx')
    """
    
    # Extraire les données de réservation
    reservations = Reservation.objects.annotate(
        month=TruncMonth('check_in')
    ).values(
        'month', 
        'property__name'
    ).annotate(
        total_revenue=Sum('total_price')
    ).order_by('month', 'property__name')

    # Convertir les données en DataFrame pandas
    df = pd.DataFrame(list(reservations))

    # Pivoter le DataFrame pour avoir les propriétés en colonnes et les mois en lignes
    pivot_df = df.pivot(index='month', columns='property__name', values='total_revenue')

    # Remplir les valeurs NaN par 0
    pivot_df = pivot_df.fillna(0)
   
    pivot_df.index = pd.to_datetime(pivot_df.index)
        # Maintenant vous pouvez utiliser strftime
    pivot_df.index = pivot_df.index.strftime('%Y-%m').tolist()
    # Ajouter une colonne de total par mois
    pivot_df['Total'] = pivot_df.sum(axis=1)

    # Ajouter une ligne de total par propriété
    pivot_df.loc['Total'] = pivot_df.sum()

    # Formater les valeurs en monnaie (par exemple, en euros)
    for col in pivot_df.columns:
        pivot_df[col] = pivot_df[col].apply(lambda x: f"€{x:.2f}")

    return pivot_df



def generate_revenue_data():
    reservations = Reservation.objects.annotate(
        month=TruncMonth('check_in')
    ).values(
        'month', 
        'property__name'
    ).annotate(
        total_revenue=Sum('total_price')
    ).order_by('month', 'property__name')

    df = pd.DataFrame(list(reservations))
    pivot_df = df.pivot(index='month', columns='property__name', values='total_revenue')
    pivot_df = pivot_df.fillna(0)

    # Préparer les données pour Chart.js
    labels = pivot_df.index.strftime('%Y-%m').tolist()
    datasets = []
    for property_name in pivot_df.columns:
        datasets.append({
            'label': property_name,
            'data': pivot_df[property_name].tolist()
        })

    # Convertir les valeurs Decimal en float
    for dataset in datasets:
        dataset['data'] = [float(value) for value in dataset['data']]

    return {
        'labels': labels,
        'datasets': datasets
    }