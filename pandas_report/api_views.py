from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from services_menage.models import Reservation, Property
from  .serializers import RevenueReportListSerializer, RevenueReportSerializer, TauxOccupationSerializer
import pandas as pd
from django.http import JsonResponse
from rest_framework import serializers
from django.db.models import F, Q

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
        
        serializer = RevenueReportSerializer(data={'dataset':data })
        

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
        raise Exception("" , result)
        serializer =  TauxOccupationSerializer(data=result_dict)
        if serializer.is_valid():
            serialized_data = serializer.data
            # Utilisez serialized_data comme nécessaire
        else:
            print(serializer.errors)
            #raise Exception("mes data", data)
        return Response(serializer.data)


    
    

    
    
