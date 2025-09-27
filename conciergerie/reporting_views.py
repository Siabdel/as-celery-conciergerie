import io
import calendar
from datetime import datetime

from django.http import FileResponse
from django.db.models import Sum, Count, F
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from conciergerie.models import Reservation, Property
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from django.http import FileResponse



class RevenueReportView(APIView):
    """Revenus totaux toutes propriétés"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        total_revenue = Reservation.objects.aggregate(total=Sum("total_price"))["total"] or 0
        revenue_by_property = (
            Reservation.objects.values("property__name")
            .annotate(total=Sum("total_price"))
            .order_by("-total")
        )
        return Response({
            "total_revenue": total_revenue,
            "by_property": list(revenue_by_property)
        })


class PropertyRevenueMonthlyView(APIView):
    """Revenu mensuel par propriété"""
    permission_classes = [IsAuthenticated]

    def get(self, request, property_id):
        property_obj = Property.objects.get(pk=property_id)
        reservations = Reservation.objects.filter(property=property_obj)

        data = {}
        for r in reservations:
            month = r.check_in.strftime("%Y-%m")
            data[month] = data.get(month, 0) + float(r.total_price)

        return Response({
            "property": property_obj.name,
            "monthly_revenue": data
        })


class OccupancyRateView(APIView):
    """Taux d’occupation par mois"""
    permission_classes = [IsAuthenticated]

    def get(self, request, property_id):
        property_obj = Property.objects.get(pk=property_id)
        reservations = Reservation.objects.filter(property=property_obj)

        today = datetime.today()
        year = today.year
        occupancy = {}

        for month in range(1, 13):
            month_days = calendar.monthrange(year, month)[1]
            reserved_days = sum(
                r.get_duration()
                for r in reservations
                if r.check_in.month == month
            )
            occupancy[calendar.month_abbr[month]] = round((reserved_days / month_days) * 100, 2)

        return Response({
            "property": property_obj.name,
            "year": year,
            "occupancy_rate": occupancy
        })


class FinancialPDFReportView(APIView):
    """Génération d’un rapport PDF"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []

        # Titre
        elements.append(Paragraph("Rapport Financier - Conciergerie", styles["Title"]))
        elements.append(Spacer(1, 20))

        # Revenus globaux
        total_revenue = Reservation.objects.aggregate(total=Sum("total_price"))["total"] or 0
        elements.append(Paragraph(f"Revenu global: {total_revenue} €", styles["Heading2"]))
        elements.append(Spacer(1, 10))

        # Tableau par propriété
        revenue_by_property = (
            Reservation.objects.values("property__name")
            .annotate(total=Sum("total_price"))
            .order_by("-total")
        )
        table_data = [["Propriété", "Revenu (€)"]] + [
            [item["property__name"], f"{item['total']:.2f}"]
            for item in revenue_by_property
        ]
        table = Table(table_data, hAlign="LEFT")
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(table)

        # Génération PDF
        doc.build(elements)
        buffer.seek(0)
        return FileResponse(buffer, as_attachment=True, filename="rapport_financier.pdf")





class RevenueReportPDFView(APIView):
    """Revenus globaux et par propriété en PDF"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []

        elements.append(Paragraph("Rapport - Revenus Globaux", styles["Title"]))
        elements.append(Spacer(1, 20))

        total_revenue = Reservation.objects.aggregate(total=Sum("total_price"))["total"] or 0
        elements.append(Paragraph(f"Revenu global: {total_revenue:.2f} €", styles["Heading2"]))
        elements.append(Spacer(1, 10))

        revenue_by_property = (
            Reservation.objects.values("property__name")
            .annotate(total=Sum("total_price"))
            .order_by("-total")
        )
        table_data = [["Propriété", "Revenu (€)"]] + [
            [item["property__name"], f"{item['total']:.2f}"] for item in revenue_by_property
        ]
        table = Table(table_data, hAlign="LEFT")
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(table)

        doc.build(elements)
        buffer.seek(0)
        return FileResponse(buffer, as_attachment=True, filename="revenus.pdf")


class PropertyRevenueMonthlyPDFView(APIView):
    """Revenu mensuel par propriété en PDF"""
    permission_classes = [IsAuthenticated]

    def get(self, request, property_id):
        property_obj = Property.objects.get(pk=property_id)
        reservations = Reservation.objects.filter(property=property_obj)

        data = {}
        for r in reservations:
            month = r.check_in.strftime("%Y-%m")
            data[month] = data.get(month, 0) + float(r.total_price)

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []

        elements.append(Paragraph(f"Rapport - Revenu Mensuel ({property_obj.name})", styles["Title"]))
        elements.append(Spacer(1, 20))

        table_data = [["Mois", "Revenu (€)"]] + [[m, f"{v:.2f}"] for m, v in data.items()]
        table = Table(table_data, hAlign="LEFT")
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(table)

        doc.build(elements)
        buffer.seek(0)
        return FileResponse(buffer, as_attachment=True,
                            filename=f"revenu_mensuel_{property_obj.id}.pdf")


class OccupancyRatePDFView(APIView):
    """Taux d’occupation par propriété en PDF"""
    permission_classes = [IsAuthenticated]

    def get(self, request, property_id):
        property_obj = Property.objects.get(pk=property_id)
        reservations = Reservation.objects.filter(property=property_obj)

        today = datetime.today()
        year = today.year
        occupancy = {}

        for month in range(1, 12 + 1):
            month_days = calendar.monthrange(year, month)[1]
            reserved_days = sum(
                r.get_duration() for r in reservations if r.check_in.month == month
            )
            occupancy[calendar.month_abbr[month]] = round((reserved_days / month_days) * 100, 2)

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []

        elements.append(Paragraph(f"Rapport - Taux d’Occupation ({property_obj.name})", styles["Title"]))
        elements.append(Spacer(1, 20))

        table_data = [["Mois", "Taux Occupation (%)"]] + [
            [month, f"{rate:.2f}%"] for month, rate in occupancy.items()
        ]
        table = Table(table_data, hAlign="LEFT")
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(table)

        doc.build(elements)
        buffer.seek(0)
        return FileResponse(buffer, as_attachment=True,
                            filename=f"taux_occupation_{property_obj.id}.pdf")



# conciergerie/reports.py
from django.db.models import Sum, Count, Q, F
from django.utils import timezone
import calendar


def revenue_per_month(property_id, year):
    """
    Returns list of dicts: [{month:1, revenue:1200}, ...]
    """
    qs = (
        Reservation.objects.filter(
            property_id=property_id,
            check_in__year=year,
            reservation_status__in=["CONFIRMED", "COMPLETED"],
        )
        .annotate(month=F("check_in__month"))
        .values("month")
        .annotate(revenue=Sum("total_price"))
        .order_by("month")
    )
    # fill missing months with 0
    data = {calendar.month_abbr[i]: 0 for i in range(1, 13)}
    for row in qs:
        data[calendar.month_abbr[row["month"]]] = row["revenue"]
    return [{"month": k, "revenue": v} for k, v in data.items()]


def occupancy_rate_monthly(year):
    """
    Global occupancy rate per month
    """
    from .models import Property
    total_units = Property.objects.filter(is_active=True).count()
    qs = (
        Reservation.objects.filter(
            check_in__year=year,
            reservation_status__in=["CONFIRMED", "COMPLETED"],
        )
        .annotate(month=F("check_in__month"))
        .values("month")
        .annotate(nights=Count("id"))
        .order_by("month")
    )
    days_in_month = {i: calendar.monthrange(year, i)[1] for i in range(1, 13)}
    data = []
    for row in qs:
        month = row["month"]
        possible_nights = total_units * days_in_month[month]
        data.append(
            {
                "month": calendar.month_abbr[month],
                "rate": round(row["nights"] / possible_nights * 100, 2),
            }
        )
    return data


def property_revenue_chart(property_id):
    """
    Simple evolution of pricing rules (for Chart.js line chart)
    """
    from .models import PricingRule
    rules = (
        PricingRule.objects.filter(property_id=property_id, is_active=True)
        .order_by("start_date")
        .values("start_date", "price_per_night")
    )
    return list(rules)