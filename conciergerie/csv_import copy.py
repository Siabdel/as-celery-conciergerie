# conciergerie/csv_import.py
from decimal import Decimal, InvalidOperation
from datetime import datetime
import logging
from django.utils import timezone
from django.db import transaction
from .models import Property, Reservation, AdditionalExpense
from core.models import ReservationStatus, PlatformChoices

logger = logging.getLogger(__name__)


def _to_decimal(value: str) -> Decimal:
    try:
        return Decimal(value.replace(",", ".").strip() or 0)
    except InvalidOperation:
        return Decimal(0)


def _to_date(value: str) -> datetime:
    # accepte 31/12/2025 ou 2025-12-31
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value.strip(), fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Date invalide : {value}")


def _to_datetime(date_part: str, hour=14, minute=0) -> datetime:
    d = _to_date(date_part)
    return timezone.make_aware(datetime(d.year, d.month, d.day, hour, minute))


from datetime import datetime

def _parse_us_date(value: str) -> datetime.date:
    """
    Accepte 9/17/2025, 09/17/2025, 2025-09-17, 17/09/2025
    Retourne datetime.date
    """
    value = value.strip()
    for fmt in ("%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Date invalide : {value}")

def import_reservations_csv(rows: list[dict], user) -> dict:
    """
    rows : liste de dict (sortie DictReader)
    user : utilisateur qui importe (pour created_by)
    Retourne {"created":int, "updated":int, "errors":list[str]}
    """
    created = updated = 0
    errors = []

    for idx, row in enumerate(rows, start=2):
        try:
            with transaction.atomic():
                # --- mapping ---
                property_name = row.get("Property", "").strip()
                prop = Property.objects.filter(name__iexact=property_name).first()
                if not prop:
                    errors.append(f"Ligne {idx} : Logement « {property_name } » introuvable")
                    continue

                check_in = _to_datetime(row.get("Date arrive Arrivée au plus tard le", ""), hour=14)
                arrival_deadline = _to_datetime(row.get("Date arrive Arrivée au plus tard le", ""), hour=23, minute=59)
                nights = int(row.get("Nb Nuits", 0) or 0)
                guest_name = row.get("Nom Voyageur", "").strip()
                currency = row.get("Devise", "EUR").strip().upper()
                amount_paid = _to_decimal(row.get("Montant Versé", 0))
                gross_revenue = _to_decimal(row.get("Revenus bruts", 0))

                # frais
                service_fee = _to_decimal(row.get("Frais de service", 0))
                quick_pay_fee = _to_decimal(row.get("Frais de paiement rapide", 0))
                cleaning_fee = _to_decimal(row.get("Frais de ménage", 0))
                linen_fee = _to_decimal(row.get("Frais pour le linge de maison", 0))

                # clé unique : property + check_in
                reservation, created_flag = Reservation.objects.update_or_create(
                    property=prop,
                    check_in=check_in,
                    defaults={
                        "check_out": check_in + timezone.timedelta(days=nights),
                        "arrival_deadline": arrival_deadline,
                        "nights": nights,
                        "guest_name": guest_name,
                        "guest_email": f"{guest_name.lower().replace(' ','')}@import.csv",  # fallback
                        "currency": currency,
                        "amount_paid": amount_paid,
                        "gross_revenue": gross_revenue or amount_paid,  # fallback
                        "platform": PlatformChoices.DIRECT,
                        "reservation_status": ReservationStatus.CONFIRMED,
                        "created_by": user,
                    }
                )
                if created_flag:
                    created += 1
                else:
                    updated += 1

                # frais annexes
                if any([service_fee, quick_pay_fee, cleaning_fee, linen_fee]):
                    AdditionalExpense.objects.update_or_create(
                        property=prop,
                        expense_type="other",
                        occurrence_date=check_in,
                        defaults={
                            "service_fee": service_fee,
                            "quick_pay_fee": quick_pay_fee,
                            "cleaning_fee": cleaning_fee,
                            "linen_fee": linen_fee,
                            "amount": service_fee + quick_pay_fee + cleaning_fee + linen_fee,
                            "description": f"Frais OTA import résa {guest_name} du {check_in:%d/%m/%Y}",
                            "created_by": user,
                        }
                    )

        except Exception as e:
            logger.exception("Import ligne %s", idx)
            errors.append(f"Ligne {idx} : {e}")

    return {"created": created, "updated": updated, "errors": errors}
