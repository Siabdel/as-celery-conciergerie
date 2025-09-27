# conciergerie/tasks.py
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings


@shared_task
def send_checkout_summary(checkout_id):
    from .models import CheckoutInventory
    checkout = CheckoutInventory.objects.get(id=checkout_id)
    subject = f"Checkout summary for {checkout.reservation}"
    message = f"""
    Cleanliness rating: {checkout.cleanliness_rating}
    Damage: {checkout.damage_description or 'None'}
    Missing items: {checkout.missing_items or 'None'}
    """
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [checkout.reservation.guest_email],
        fail_silently=False,
    )
