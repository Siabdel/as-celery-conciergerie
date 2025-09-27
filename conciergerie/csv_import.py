# conciergerie/csv_import.py
import logging
import pandas as pd
from decimal import Decimal, InvalidOperation
from datetime import datetime
from django.utils import timezone
from django.db import transaction
from .models import Property, Reservation, AdditionalExpense
from core.models import ResaStatus, PlatformChoices

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
        df = pd.read_csv(file_obj, dtype=str).fillna("")  # toutes les colonnes string d'abord
    except Exception as e:
        return {"created": 0, "updated": 0, "errors": [f"CSV illisible : {e}"]}

    # on renomme proprement
    df.columns = (
        df.columns.str.strip()  # enlève espaces
        .str.lower()
        .str.replace(" ", "_")
        .str.replace("/", "_")
    )

    # mapping rapide
    col_map = {
        "date": "date",
        "arrivée_au_plus_tard_le": "arrival_deadline_str",
        "date_de_début": "check_in_str",
        "date_de_fin": "check_out_str",
        "nuits": "nights",
        "voyageur": "guest_name",
        "property": "property_name",
        "devise": "currency",
        "montant": "amount_paid",
        "versé": "paid_str",  # ignoré ici (déjà dans montant)
        "frais_de_service": "service_fee",
        "frais_de_paiement_rapide": "quick_pay_fee",
        "frais_de_ménage": "cleaning_fee",
        "frais_pour_le_linge_de_maison": "linen_fee",
        "revenus_bruts": "gross_revenue",
    }

    for col in col_map.values():
        if col not in df.columns:
            df[col] = ""

    # conversion en types natifs
    df["check_in"] = pd.to_datetime(df["check_in_str"], errors="coerce").dt.date
    df["check_out"] = pd.to_datetime(df["check_out_str"], errors="coerce").dt.date
    df["arrival_deadline"] = pd.to_datetime(df["arrival_deadline_str"], errors="coerce").dt.date
    df["nights"] = pd.to_numeric(df["nights"], errors="coerce").astype("Int64")
    df["amount_paid"] = df["amount_paid"].apply(_to_decimal)
    df["service_fee"] = df["service_fee"].apply(_to_decimal)
    df["quick_pay_fee"] = df["quick_pay_fee"].apply(_to_decimal)
    df["cleaning_fee"] = df["cleaning_fee"].apply(_to_decimal)
    df["linen_fee"] = df["linen_fee"].apply(_to_decimal)
    df["gross_revenue"] = df["gross_revenue"].apply(_to_decimal)

    # itération ligne à ligne
    for idx, row in df.iterrows():
        try:
            with transaction.atomic():
                # --- Property ---
                prop = Property.objects.filter(name__iexact=row["property_name"].strip()).first()
                if not prop:
                    errors.append(f"Ligne {idx+2} : Property « {row['property_name']} » inconnu")
                    continue

                # --- dates obligatoires ---
                if pd.isna(row["check_in"]) or pd.isna(row["check_out"]):
                    errors.append(f"Ligne {idx+2} : dates manquantes")
                    continue

                check_in_dt = timezone.make_aware(
                    datetime.combine(row["check_in"], datetime.min.time())
                ).replace(hour=14)
                check_out_dt = timezone.make_aware(
                    datetime.combine(row["check_out"], datetime.min.time())
                ).replace(hour=11)

                # deadline facultative
                arrival_deadline = None
                if not pd.isna(row["arrival_deadline"]):
                    arrival_deadline = timezone.make_aware(
                        datetime.combine(row["arrival_deadline"], datetime.min.time())
                    ).replace(hour=23, minute=59)

                # --- création / mise à jour ---
                reservation, created_flag = Reservation.objects.update_or_create(
                    property=prop,
                    check_in=check_in_dt,
                    defaults={
                        "check_out": check_out_dt,
                        "arrival_deadline": arrival_deadline,
                        "nights": row["nights"] or (row["check_out"] - row["check_in"]).days,
                        "guest_name": row["guest_name"].strip(),
                        "guest_email": f"{row['guest_name'].lower().replace(' ','')}@csv.import",
                        "currency": row["currency"] or "MAD",
                        "amount_paid": row["amount_paid"],
                        "gross_revenue": row["gross_revenue"] or row["amount_paid"],
                        "platform": PlatformChoices.DIRECT,
                        "reservation_status": ResaStatus.CONFIRMED,
                        "created_by": user,
                    }
                )
                if created_flag:
                    created += 1
                else:
                    updated += 1

                # --- AdditionalExpense pour les frais ---
                total_fees = row["service_fee"] + row["quick_pay_fee"] + row["cleaning_fee"] + row["linen_fee"]
                if total_fees:
                    AdditionalExpense.objects.update_or_create(
                        property=prop,
                        expense_type="other",
                        occurrence_date=row["check_in"],
                        defaults={
                            "service_fee": row["service_fee"],
                            "quick_pay_fee": row["quick_pay_fee"],
                            "cleaning_fee": row["cleaning_fee"],
                            "linen_fee": row["linen_fee"],
                            "amount": total_fees,
                            "description": f"Frais CSV – résa {row['guest_name']} du {row['check_in']}",
                            "created_by": user,
                        }
                    )

        except Exception as e:
            logger.exception("Ligne %s", idx+2)
            errors.append(f"Ligne {idx+2} : {e}")

    return {"created": created, "updated": updated, "errors": errors}
