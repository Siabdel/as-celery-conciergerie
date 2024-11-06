from django.shortcuts import render
##
from django.db.models import Sum
from slick_reporting.views import ReportView, Chart
from slick_reporting.fields import ComputationField
from .models import MySalesItems

class ProductSales(ReportView):
    report_model = MySalesItems
    date_field = "date_placed"
    group_by = "product"
    columns = [
        "title",
        ComputationField.create(
            method=Sum, 
            field="value", 
            name="value__sum", 
            verbose_name="Total vendu $"
        ),
    ]
    chart_settings = [
        Chart(
            "Total vendu $",
            Chart.BAR,
            data_source=["value__sum"],
            title_source=["title"],
        ),
    ]

""" 
Rapport avec série temporelle
Pour un rapport mensuel des ventes par produit 
"""
class MonthlyProductSales(ReportView):
    report_model = MySalesItems
    date_field = "date_placed"
    group_by = "product"
    columns = ["name", "sku"]
    time_series_pattern = "monthly"
    time_series_columns = [
        ComputationField.create(
            Sum, "value", verbose_name="Valeur des ventes", name="value"
        )
    ]
    chart_settings = [
        Chart(
            "Total des ventes mensuelles",
            Chart.PIE,
            data_source=["value"],
            title_source=["name"]
        ),
    ]
    
""" 
Rapport en tableau croisé
Pour créer un tableau croisé dynamique :
"""
class MyCrosstabReport(ReportView):
    crosstab_field = "client"
    crosstab_ids = [1, 2, 3]
    crosstab_columns = [
        ComputationField.create(Sum, "value", verbose_name="Total")
    ]
    
from slick_reporting.generator import ReportGenerator
from .models import MySalesModel

class MyCustomReport(ReportGenerator):
    report_model = MySalesModel
    group_by = "product"
    columns = ["title", "__total__"]

    def custom_calculation(self):
        # Ajoutez ici votre logique personnalisée
        pass

my_report = MyCustomReport()
data = my_report.get_report_data()


""" 
Pour des calculs personnalisés ou des rapports plus complexes, vous pouvez utiliser directement 
le ReportGenerator :
"""

from slick_reporting.generator import ReportGenerator
from .models import MySalesModel

class MyCustomReport(ReportGenerator):
    report_model = MySalesModel
    group_by = "product"
    columns = ["title", "__total__"]

    def custom_calculation(self):
        # Ajoutez ici votre logique personnalisée
        pass

my_report = MyCustomReport()
data = my_report.get_report_data()