from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from services_menage.models import Reservation, Property
import pandas_report.serializers as pd_serializer
import pandas as pd
from django.http import JsonResponse
from rest_framework import serializers
from django.db.models import F, Q
from rest_framework.decorators import api_view
from datetime import datetime, timedelta


def month_name_fr(month_number):
    months_fr = {
        1: 'Janvier', 2: 'Février', 3: 'Mars', 4: 'Avril',
        5: 'Mai', 6: 'Juin', 7: 'Juillet', 8: 'Août',
        9: 'Septembre', 10: 'Octobre', 11: 'Novembre', 12: 'Décembre'
    }
    return months_fr.get(month_number, '')

class RevenueReportAPIView(APIView):
    ## get()
    def get(self, request):
        reservations = Reservation.objects.annotate(
            month=TruncMonth('check_in')
        ).values(
            'month', 
            'property__name'
        ).annotate(
            total_revenue=Sum('total_price')
        ).order_by('property__name', 'month')

        df = pd.DataFrame(reservations)
        
        if not df.empty:
            df['month'] = pd.to_datetime(df['month'])
            pivot_df = df.pivot(index='property__name', columns='month', values='total_revenue')
            pivot_df = pivot_df.fillna(0)

            # Ajouter une colonne de total par propriété
            pivot_df['Total'] = pivot_df.sum(axis=1)  
            
            ## les libelles columns et index
            json_data = []
            data = []
            libelles = {'columns' : pivot_df.columns , 'index' : pivot_df.index}


            for property_name in pivot_df.index:
                property_data = {
                    'property_name': property_name,
                    'revenues': [],
                    'total'  : 0,
                }
                lignes_revenue = {}
                for month in pivot_df.columns:
                    if month != 'Total':
                        month_str = f"{month_name_fr(month.month)} {month.year}"
                        lignes_revenue.update(
                                    {
                                     month_str : float(pivot_df.loc[property_name, month])
                                    })
                # total par ligne 
                property_data['total'] = float(pivot_df.loc[property_name].sum()) 
                ## ajouter la ligne
                property_data['revenues'] = lignes_revenue 
                ##
                data.append(property_data)
                
          
        # Ajouter une ligne de total pour tous les mois
        else:
            data = []

        json_data.append({'dataset' : data})
        json_data.append({'libelles' : libelles })
        
        serializer = pd_serializer.RevenueReportSerializer(data={'dataset':data })
        

        if serializer.is_valid():
            serialized_data = serializer.data
            # Utilisez serialized_data comme nécessaire
        else:
            print(serializer.errors)
            #raise Exception("mes data", data)
    
        return Response(serializer.data)

        

        
class TauxOccupationAPIView(APIView):
    """ 
    obtenir le nombre de jours réservés par mois pour chaque propriété avec la bibliothèque Pandas, nous devons :
    Récupérer les données depuis Django ORM.
    Convertir les données en un DataFrame Pandas.
    Calculer les jours réservés pour chaque réservation.
    Grouper les données par mois et propriété pour obtenir la somme des jours réservés.
    """
    
    def get(self, request):

        # Récupérer les données avec Django ORM
        reservations = Reservation.objects.annotate(
            property_name=F('property__name')
        ).values('property_name', 'check_in', 'check_out')

        # Convertir les données en DataFrame Pandas
        df = pd.DataFrame(list(reservations))
        # Convertir check_in et check_out en datetime pour les calculs
        df['check_in'] = pd.to_datetime(df['check_in'])
        df['check_out'] = pd.to_datetime(df['check_out'])

        # Calculer le nombre de jours réservés pour chaque réservation
        df['days_reserved'] = (df['check_out'] - df['check_in']).dt.days
        # Extraire l'année et le mois
        df['month'] = df['check_in'].dt.to_period('M')
        df['month'] = str(df['month']) 
        # Grouper les données et calculer le total des jours réservés
        result = df.groupby(['month', 'property_name'])['days_reserved'].sum().reset_index()

        # Renommer les colonnes pour plus de clarté
        result.columns = ['Month', 'Property', 'Total Days Reserved']
        # Convertir le DataFrame en dictionnaire
        result_dict = { 'datatest': [
                {'month': '2024-01', 'property_name': 'Property A', 'total_days_reserved': 45},
                {'month': '2024-01', 'property_name': 'Property B', 'total_days_reserved': 30},
                {'month': '2024-02', 'property_name': 'Property A', 'total_days_reserved': 20},
                # Ajoutez d'autres entrées si nécessaire
            ]
        }
        
        # Conversion du DataFrame en liste de dictionnaires
        result_dict = {
            'datatest': result.rename(columns={
                'Month': 'month',
                'Property': 'property_name',
                'Total Days Reserved': 'total_days_reserved'
            }).to_dict(orient='records')
        }
        ## to json 
        # raise Exception("" , result)
        serializer = pd_serializer.TauxOccupationSerializer(data=result_dict)
        if serializer.is_valid():
            serialized_data = serializer.data
            # Utilisez serialized_data comme nécessaire
        else:
            print(serializer.errors)
            #raise Exception("mes data", data)
        return Response(serializer.data)


    
    
@api_view(['GET'])
def property_revenue_by_month(request, property_id):
    # Récupérer toutes les réservations pour la propriété donnée
    reservations = Reservation.objects.filter(property_id=property_id)
    
    # Créer un DataFrame pandas à partir des réservations
    df = pd.DataFrame(list(reservations.values('check_in', 'check_out', 'total_price')))
    
    # Convertir les dates en objets datetime
    df['check_in'] = pd.to_datetime(df['check_in'])
    df['check_out'] = pd.to_datetime(df['check_out'])
    
    # Créer une série de dates pour chaque jour de séjour
    date_range = pd.date_range(start=df['check_in'].min(), end=df['check_out'].max())
    
    # Initialiser un DataFrame pour stocker les revenus quotidiens
    # Initialiser un DataFrame pour stocker les revenus quotidiens
    daily_revenue = pd.DataFrame(index=date_range, columns=['revenue'])
    daily_revenue['revenue'] = 0.0  # Initialiser avec des flottants

    # Calculer le revenu quotidien pour chaque réservation
    for _, row in df.iterrows():
        days = (row['check_out'] - row['check_in']).days
        daily_price = float(row['total_price']) / days  # Convertir en float
        date_range = pd.date_range(start=row['check_in'], end=row['check_out'] - timedelta(days=1))
        daily_revenue.loc[date_range, 'revenue'] += daily_price

    # ... (le reste du code reste inchangé)
    # Regrouper par mois et calculer le revenu mensuel
    monthly_revenue = daily_revenue.resample('ME').sum()
    
    # Formater les résultats
    result = monthly_revenue.reset_index()
    result['month'] = result['index'].dt.strftime('%Y-%B')
    # Arrondir le revenu à 10.2
    result['revenue'] = result['revenue'].apply(lambda x: round(x, 1))  #
    result = result[['month', 'revenue']]
    ## result_dict = result.to_dict('records')  # Encapsuler dans un dictionnaire

    # Conversion du DataFrame en liste de dictionnaires
    result_dict = {
        'dataset': result.rename(columns={
            'Month': 'month',
            'Revenue': 'revenue',
        }).to_dict(orient='records')
    }

    ## raise Exception("" , result_dict2)
    serializer =  pd_serializer.RevenuePropriotytSerializer(data=result_dict)
    ## 
    if serializer.is_valid():
        serialized_data = serializer.data
        # Utilisez serialized_data comme nécessaire
    else:
        print(serializer.errors)
        #raise Exception("mes data", data)
    return Response(serializer.data)




@api_view(['GET'])
def property_occupancy_rate_by_month(request, property_id):
    # Récupérer toutes les réservations pour la propriété donnée
    reservations = Reservation.objects.filter(property_id=property_id)
    
    # Créer un DataFrame pandas à partir des réservations
    df = pd.DataFrame(list(reservations.values('check_in', 'check_out')))
    
    if df.empty:
        return Response({'message': 'Aucune réservation trouvée pour cette propriété.'})
    
    # Convertir les dates en objets datetime
    df['check_in'] = pd.to_datetime(df['check_in'])
    df['check_out'] = pd.to_datetime(df['check_out'])
    
    # Déterminer la plage de dates à analyser
    start_date = df['check_in'].min().replace(day=1)
    end_date = df['check_out'].max() + pd.offsets.MonthEnd(0)
    
    # Créer un DataFrame pour chaque jour de la période
    date_range = pd.date_range(start=start_date, end=end_date)
    daily_occupancy = pd.DataFrame(index=date_range, columns=['occupied'])
    daily_occupancy['occupied'] = 0
    
    # Marquer les jours occupés
    for _, row in df.iterrows():
        mask = (daily_occupancy.index >= row['check_in']) & (daily_occupancy.index < row['check_out'])
        daily_occupancy.loc[mask, 'occupied'] = 1
    
    # Calculer le taux d'occupation mensuel
    monthly_occupancy = daily_occupancy.resample('M').mean()
    monthly_occupancy['occupancy_rate'] = monthly_occupancy['occupied'] * 100
    
    # Formater les résultats
    result = monthly_occupancy.reset_index()
    result['month'] = result['index'].dt.strftime('%Y-%B')
    result = result[['month', 'occupancy_rate']]
    result['occupancy_rate'] = result['occupancy_rate'].round(2)
    result_dict = {'occupancy_data': result.to_dict('records')}
    
     # Utiliser le sérialiseur
    serializer =  pd_serializer.OccupancyDataSerializer(data={'dataset': result.to_dict('records')})
    if serializer.is_valid():
        return Response(serializer.data)
    else:
        return Response(serializer.errors, status=400)
    
    return Response(result_dict)