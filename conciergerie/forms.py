# conciergerie/forms.py
import csv
import io
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

class ReservationImportForm(forms.Form):
    csv_file = forms.FileField(
        label=_("Fichier CSV (séparateur virgule)"),
        help_text=_("Colonnes attendues : Date reservation,Date arrive Arrivée au plus tard le,Nb Nuits,Nom Voyageur,Property Logement,Devise,Montant Versé,Frais de service,Frais de paiement rapide,Frais de ménage,Frais pour le linge de maison,Revenus bruts")
    )

    def clean_csv_file(self):
        f = self.cleaned_data["csv_file"]
        if not f.name.lower().endswith(".csv"):
            raise ValidationError(_("Le fichier doit avoir l'extension .csv"))
        return f

    def read(self):
        """Return list[dict] ready for importer"""
        file = self.cleaned_data["csv_file"]
        decoded_file = file.read().decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(decoded_file))
        return list(reader)



class CheckoutInventoryForm(forms.Form):
    pass