
import os
import pandas as pd
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth.models import User
from conciergerie.models import Reservation, Property
from core.models import ReservationStatus, PlatformChoices
import pandas as pd
import numpy as np
from decimal import Decimal, InvalidOperation

 # ---------- 2. Conversion Decimal SÛRE ----------
def safe_dec(val):
    try:
        return Decimal(str(val))
    except (InvalidOperation, ValueError, TypeError):
        return Decimal("0")


class Command(BaseCommand):
    help = "Importe les réservations depuis un CSV (format %Y%m%d)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            help="Chemin vers le fichier CSV à importer",
            required=True,
        )

    def handle(self, *args, **options):
        file_path = options["file"]

        if not os.path.isfile(file_path):
            self.stdout.write(self.style.ERROR(f"Fichier introuvable : {file_path}"))
            return

        # 1. Charger le CSV
        df = pd.read_csv(file_path, delimiter=",", encoding="utf-8")

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
            "Frais de menage": "cleaning_fee",
            "Frais pour le linge de maison": "frais_linge",
            "Revenus bruts": "revenus_bruts"
        }, inplace=True)

        # 3. Convertir les dates au format %Y%m%d
        date_cols = ["date_reservation", "check_in", "check_out"]
        for col in date_cols:
            print(f"Nettoyage de la colonne {col} avant conversion :", df[col])
            # Supprimer les caractères non numériques avant la conversion
            df[col] = df[col].astype(str).str.replace(r"[^\d]", "", regex=True)
            df[col] = pd.to_datetime(df[col], format="%Y%m%d")
            
        print("Données après nettoyage :", df.head)

        # 4. Nettoyer les montants
        montant_cols = ["total_price", "service_fee", "cleaning_fee", "frais_linge", "revenus_bruts"]
        for col in montant_cols:
            df[col] = df[col].astype(str).str.replace(",", ".").astype(float)
        ## --- VERSION AVANCEE SURE ET ROBUSTE ---

        # ---------- 1. Nettoyer les montants ----------
        montant_cols = ["total_price", "service_fee", "cleaning_fee", "frais_linge", "montant_verse", "revenus_bruts"]

        for col in montant_cols:
            # → string, remplace , par .
            # string → remplace , par .
            df[col] = (
                df[col]
                .astype(str)
                .str.replace(",", ".", regex=False)
            ) 
            # → float, puis remplace vrais NaN / inf par 0
            df[col] = pd.to_numeric(df[col], errors="coerce")  # np.nan si impossible
            df[col] = df[col].replace([np.inf, -np.inf], np.nan).fillna(0)
            # convertit en float, puis NaN / inf → 0

       
       
        # 5. Supprimer les lignes avec dates invalides
        df = df.dropna(subset=["check_in", "check_out"])

        # 6. Fonction utilitaire
        def make_aware_safe(dt):
            if pd.isna(dt):
                return None
            dt = dt.to_pydatetime()
            if timezone.is_naive(dt):
                dt = timezone.make_aware(dt)
            return dt
        # 7. Fonction agency par defaut
        from core.models import Agency
        # dans la boucle
        ##agency = Agency.objects.filter(is_active=True).first(),  # <-- obligatoire
        agency, created = Agency.objects.get_or_create( name="Netatlass Conciergerie", defaults={...})
        print("Agence utilisée pour l'import :", agency)


        # 8. Parcourir et insérer
        count_created = 0
        for _, row in df.iterrows():
            check_in = make_aware_safe(row["check_in"])
            check_out = make_aware_safe(row["check_out"])
             # ---------- 3. Utilisation dans la boucle ----------
            defaults = {
                "total_price": safe_dec(row["total_price"]),
                "cleaning_fee": safe_dec(row["cleaning_fee"]),
                "service_fee":  safe_dec(row["service_fee"]),
            }


            if check_in is None or check_out is None:
                continue

            propriete, _ = Property.objects.get_or_create(
                #agency = agency,  # <-- obligatoire
                name=row["property_name"],
                defaults={
                    "agency": agency,
                    "owner": User.objects.first(),
                    "type": "apartment",
                    "address": "Adresse non renseignée",
                    "latitude": 0.0,
                    "longitude": 0.0,
                    "price_per_night": 100.00,
                }
            )

            _, created = Reservation.objects.get_or_create(
                #agency=agency,  # <-- obligatoire
                property=propriete,
                check_in=check_in,
                check_out=check_out,
                
                # 1)  Choose ONE agency (CLI argument or settings)
                #agency = Agency.objects.first(),

                defaults = {
                    "agency": agency,
                    "reservation_status": ReservationStatus.CONFIRMED,
                    "guest_name": row["guest_name"],
                    "guest_email": row.get("guest_email") or "toto@example.com",
                    "platform": PlatformChoices.DIRECT,
                    "number_of_guests": 1,
                    "total_price": Decimal(str(row["total_price"] or 0.0)),
                    "cleaning_fee": Decimal(str(row["cleaning_fee"] or 0.0)),
                    "service_fee": Decimal(str(row["service_fee"] or 0.0)),
                    "currency" : row.get("devise", "EUR")[:3],  # keep 3 letters
                    "amount_paid": Decimal(str(row["montant_verse"] or 0.0)),
                    # gross_revenue & nights are auto-computed if left 0 / None
                }
            )
            if created:
                count_created += 1

        self.stdout.write(self.style.SUCCESS(f"{count_created} réservations importées avec succès."))