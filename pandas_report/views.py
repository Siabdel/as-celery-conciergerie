import json
from django.shortcuts import render
import pandas as pd
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from services_menage.models import Reservation, Property
from django.http import JsonResponse
from django.views.generic import TemplateView
from .report import generate_revenue_data, generate_revenue_report

#-------------------------------------------
#--- Revenue Chart View
#-------------------------------------------
class RevenueChartView(TemplateView):
    template_name = 'revenue_mensuel.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['chart_data'] = generate_revenue_data()
        return context

#-------------------------------------------
#--- Revenue data
#-------------------------------------------
def revenue_data(request):
    data = generate_revenue_data()
    return JsonResponse(data)


def revenue_report_data(request):
    """
        une vue et un template pour afficher le rapport de revenus généré par la fonction generate_revenue_report().
        Voici comment vous pouvez procéder :

    """
    report = generate_revenue_report()
    data = {
        'index': report.index.strftime('%Y-%m').tolist(),
        'columns': report.columns.tolist(),
        'data': report.values.tolist()
    }
    return JsonResponse(data)


class RevenueReportView(TemplateView):
    template_name = 'revenue_report.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        report = generate_revenue_report()
        # Assurez-vous que l'index est un DatetimeIndex
        data = { 'report_data' : 
                        json.dumps({
                            'index': report.index.tolist(),
                            'columns': report.columns.tolist(),
                            'data': report.values.tolist()
                        } )
        }
        ## raise Exception("report = ", data)
        
        return data
    
#-------------------------------------------
#--- Revenue
#-------------------------------------------
class ConciergerieRevenueView(TemplateView):
    template_name = 'vuejs/vuejs_revenue_report.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['dataset'] = generate_revenue_data()
        return context

