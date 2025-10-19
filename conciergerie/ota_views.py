from django.shortcuts import render


# conciergerie/ota_webhooks/views.py
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from conciergerie.models import Property, Reservation
from conciergerie.serializers import ReservationSerializer
from conciergerie.serializers import AirbnbWebhookSerializer, BookingWebhookSerializer
from conciergerie.ota_webhooks.signatures import verify_airbnb, verify_booking
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def _ota_save_reservation(property_id, platform, reservation_id,
                          start, end, guest_name, guest_email,
                          guests, status_map):
    """
    Create or update reservation in a transaction-safe way.
    status_map: OTA status -> our ReservationStatus
    """
    prop = get_object_or_404(Property, id=property_id)
    defaults = {
        "check_in": timezone.make_aware(datetime.combine(start, datetime.min.time())).replace(hour=14),
        "check_out": timezone.make_aware(datetime.combine(end, datetime.min.time())).replace(hour=11),
        "guest_name": guest_name,
        "guest_email": guest_email,
        "number_of_guests": guests,
        "platform": platform,
        "reservation_status": status_map,
        "total_price": prop.total_price_for_range(
            timezone.make_aware(datetime.combine(start, datetime.min.time())),
            timezone.make_aware(datetime.combine(end, datetime.min.time()))
        ),
    }
    reservation, created = Reservation.objects.update_or_create(
        property=prop,
        check_in=defaults["check_in"],
        defaults=defaults,
    )
    return reservation, created


@api_view(["POST"])
@permission_classes([AllowAny])  # HMAC check replaces auth
def airbnb_webhook(request):
    signature = request.headers.get("X-Airbnb-Signature", "")
    secret = settings.AIRBNB_WEBHOOK_SECRET
    if not verify_airbnb(request.body, signature, secret):
        logger.warning("Airbnb webhook invalid signature")
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    ser = AirbnbWebhookSerializer(data=request.data)
    if not ser.is_valid():
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

    data = ser.validated_data
    if data["status"] == "cancelled":
        # soft-delete by setting status
        try:
            resa = Reservation.objects.get(
                property__ota_airbnb_id=data["listing_id"],
                check_in=data["start_date"],
                guest_email=data["guest"]["email"],
            )
            resa.reservation_status = "CANCELLED"
            resa.save(update_fields=["reservation_status"])
            return Response(status=status.HTTP_200_OK)
        except Reservation.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

    # accepted or modified
    prop, created = Property.objects.get_or_create(
        ota_airbnb_id=data["listing_id"],
        defaults={
            "name": f"Airbnb {data['listing_id']}",
            "type": "apartment",
            "owner_id": settings.DEFAULT_OWNER_ID,  # fallback owner
            "price_per_night": 100,  # will be overridden by pricing rules
        }
    )
    reservation, created = _ota_save_reservation(
        property_id=prop.id,
        platform="AIRBNB",
        reservation_id=data["reservation_id"],
        start=data["start_date"],
        end=data["end_date"],
        guest_name=f"{data['guest']['first_name']} {data['guest']['last_name']}",
        guest_email=data["guest"]["email"],
        guests=data["number_of_guests"],
        status_map="CONFIRMED",
    )
    return Response(
        {"reservation_id": reservation.id, "created": created},
        status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def booking_webhook(request):
    signature = request.headers.get("X-Booking-Signature", "")
    secret = settings.BOOKING_WEBHOOK_SECRET
    if not verify_booking(request.body, signature, secret):
        logger.warning("Booking.com webhook invalid signature")
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    ser = BookingWebhookSerializer(data=request.data)
    if not ser.is_valid():
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

    data = ser.validated_data
    if data["status"] == "cancelled":
        try:
            resa = Reservation.objects.get(
                property__ota_booking_id=data["hotel_id"],
                check_in=data["arrival_date"],
                guest_email=data["customer"]["email"],
            )
            resa.reservation_status = "CANCELLED"
            resa.save(update_fields=["reservation_status"])
            return Response(status=status.HTTP_200_OK)
        except Reservation.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

    prop, created = Property.objects.get_or_create(
        ota_booking_id=data["hotel_id"],
        defaults={
            "name": f"Booking {data['hotel_id']}",
            "type": "apartment",
            "owner_id": settings.DEFAULT_OWNER_ID,
            "price_per_night": 100,
        }
    )
    reservation, created = _ota_save_reservation(
        property_id=prop.id,
        platform="BOOKING",
        reservation_id=data["reservation_id"],
        start=data["arrival_date"],
        end=data["departure_date"],
        guest_name=f"{data['customer']['first_name']} {data['customer']['last_name']}",
        guest_email=data["customer"]["email"],
        guests=data["guest_count"],
        status_map="CONFIRMED",
    )
    return Response(
        {"reservation_id": reservation.id, "created": created},
        status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
    )