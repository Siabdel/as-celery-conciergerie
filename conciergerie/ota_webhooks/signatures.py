# conciergerie/ota_webhooks/signatures.py
import hmac
import hashlib
import base64
from django.conf import settings


def verify_airbnb(payload: bytes, signature: str, secret: str) -> bool:
    """
    Airbnb sends header  X-Airbnb-Signature: sha256=<base64 digest>
    """
    if not signature.startswith("sha256="):
        return False
    digest = signature[7:]  # remove prefix
    mac = base64.b64encode(
        hmac.new(
            secret.encode(), payload, hashlib.sha256
        ).digest()
    ).decode()
    return hmac.compare_digest(mac, digest)


def verify_booking(payload: bytes, signature: str, secret: str) -> bool:
    """
    Booking.com sends header  X-Booking-Signature: <hex digest>
    """
    mac = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(mac, signature)