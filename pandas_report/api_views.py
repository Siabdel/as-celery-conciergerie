from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from services_menage.models import Reservation, Property
from  .serializers import RevenueReportListSerializer, RevenueReportSerializer
import pandas as pd
from django.http import JsonResponse
from rest_framework import serializers

def month_name_fr(month_number):
    months_fr = {
        1: 'Janvier', 2: 'Février', 3: 'Mars', 4: 'Avril',
        5: 'Mai', 6: 'Juin', 7: 'Juillet', 8: 'Août',
        9: 'Septembre', 10: 'Octobre', 11: 'Novembre', 12: 'Décembre'
    }
    return months_fr.get(month_number, '')

class RevenueReportAPIView(APIView):
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

        