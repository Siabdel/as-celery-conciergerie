# staff/signals.py
from django.db.models.signals import pre_save
from django.dispatch import receiver
from staff.models import Employee
from django.contrib.auth import get_user_model

User = get_user_model()


@receiver(pre_save, sender=Employee)
def auto_link_employee(sender, instance, **kwargs):
    """Crée l’Employee même si l’utilisateur n’a pas encore de profil."""
    if not instance.pk:                    # création uniquement
        # on récupère l’agence du manager qui sauvegarde
        # (transmise via save_model)
        if not instance.agency_id:
            # fallback si jamais non remplie
            from django.contrib.auth.models import AnonymousUser
            from django.core.exceptions import PermissionDenied

            # on récupère l’agence du manager connecté (via thread local ou save_model)
            # Ici on suppose que save_model a déjà rempli instance.agency
            pass   # déjà rempli via save_model