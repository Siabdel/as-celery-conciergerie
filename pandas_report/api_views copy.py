
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from services_menage.models import Reservation, Property
from .serializers import RevenueReportSerializer
import pandas as pd

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

            data = []
            for property_name in pivot_df.index:
                revenues = {}
                for month in pivot_df.columns:
                    month_str = f"{month_name_fr(month.month)} {month.year}"
                    revenues[month_str] = float(pivot_df.loc[property_name, month])
                
                total = sum(revenues.values())
                
                property_data = {
                    'property_name': property_name,
                    'revenues': revenues,
                    'total': total
                }
                data.append(property_data)

        else:
            data = []

        serializer = RevenueReportSerializer(data, many=True)
        return Response(serializer.data)