# conciergerie/csv_import.py
import logging
import pandas as pd
from decimal import Decimal, InvalidOperation
from datetime import datetime
from django.utils import timezone
from django.db import transaction
from .models import Property, Reservation, AdditionalExpense
from core.models import ReservationStatus, PlatformChoices

logger = logging.getLogger(__name__)


## res = import_reservations_csv_pandas(request.FILES["csv_file"], request.user)
def _to_decimal(x) -> Decimal:
    """Convert pandas float / string with comma -> Decimal."""
    if pd.isna(x):
        return Decimal(0)
    try:
        return Decimal(str(x).replace(",", ".").replace(" ", ""))
    except InvalidOperation:
        return Decimal(0)


def _to_date(x) -> datetime.date:
    """Accept 2025/09/11 or 2025-09-11."""
    if pd.isna(x):
        return None
    return pd.to_datetime(x, dayfirst=False).date()


def import_reservations_csv_pandas(file_obj, user) -> dict:
    """
    file_obj : InMemoryUploadedFile
    user     : request.user (for created_by)
    Return   : {"created":int, "updated":int, "errors":list[str]}
    """
    created = updated = 0
    errors = []

    # --- lecture + nettoyage pandas ---
    try:
        df = pd.read_table(file_obj, dtype=str).fillna("")  # toutes les colonnes string d'abord
    except Exception as e:
        return {"created": 0, "updated": 0, "errors": [f"CSV illisible !!!!: {e}"]}


    import pandas as pd
    import os
    import django
    from decimal import Decimal
    from django.contrib.auth.models import User
    from conciergerie.models import Reservation, Property
    from core.models import ReservationStatus, PlatformChoices

    # Django setup
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "your_project.settings")
    django.setup()

    # 1. Charger le CSV
    df = pd.read_csv("reservations_conciergerie.csv", delimiter=",", encoding="utf-8")

    # 2. Renommer les colonnes
    df.rename(columns={
        "Date": "date_reservation",
       
        "Date de début": "check_in",
        "Date de fin": "check_out",
        "Nuits": "nb_nuits",
        "Voyageur": "guest_name",
        "Property": "property_name",
        "Devise": "devise",
        "Montant": "total_price",
        "Versé": "montant_verse",
        "Frais de service": "service_fee",
        "Frais de paiement rapide": "frais_paiement_rapide",
        "Frais de ménage": "cleaning_fee",
        "Frais pour le linge de maison": "frais_linge",
        "Revenus bruts": "revenus_bruts"
    }, inplace=True)

    # 3. Convertir les dates au format %Y%m%d
    date_cols = ["date_reservation", "date_arrivee_max", "check_in", "check_out"]
    for col in date_cols:
        df[col] = pd.to_datetime(df[col], format="%Y%m%d", errors="coerce")

    # 4. Nettoyer les montants
    montant_cols = ["total_price", "service_fee", "cleaning_fee", "frais_linge", "revenus_bruts"]
    for col in montant_cols:
        df[col] = df[col].astype(str).str.replace(",", ".").astype(float)

    # 5. Supprimer les lignes avec dates invalides
    df = df.dropna(subset=["check_in", "check_out"])

    # 6. Parcourir et insérer
    for _, row in df.iterrows():
        check_in = row["check_in"].to_pydatetime()
        check_out = row["check_out"].to_pydatetime()

        propriete, _ = Property.objects.get_or_create(
            name=row["property_name"],
            defaults={
                "owner": User.objects.first(),
                "type": "apartment",
                "address": "Adresse non renseignée",
                "latitude": 0.0,
                "longitude": 0.0,
                "price_per_night": 100.00,
            }
        )

        Reservation.objects.get_or_create(
            property=propriete,
            check_in=check_in,
            check_out=check_out,
            defaults={
                "reservation_status": ReservationStatus.CONFIRMED,
                "guest_name": row["guest_name"],
                "guest_email": "inconnu@example.com",
                "platform": PlatformChoices.DIRECT,
                "number_of_guests": 1,
                "total_price": Decimal(str(row["total_price"])),
                "cleaning_fee": Decimal(str(row["cleaning_fee"])),
                "service_fee": Decimal(str(row["service_fee"])),
            }
        )

    print("✅ Import terminé.")

    return {"created": created, "updated": updated, "errors": errors}
