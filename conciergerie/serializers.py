
from rest_framework import serializers
from conciergerie.models import Property, Reservation, ServiceTask, Incident, AdditionalExpense
from staff.models import Employee
from datetime import datetime



class PropertySerializer(serializers.ModelSerializer):
    owner = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Property
        fields = [
            "id", "name", "type", "owner", "price_per_night",
            "address", "latitude", "longitude", "capacity"
        ]


class ReservationSerializer(serializers.ModelSerializer):
    property = serializers.StringRelatedField()
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Reservation
        fields = [
            "id", "property", "check_in", "check_out", "guest_name",
            "guest_email", "platform", "number_of_guests",
            "total_price", "cleaning_fee", "service_fee", "reservation_status"
        ]


class ServiceTaskSerializer(serializers.ModelSerializer):
    employee = serializers.StringRelatedField()
    property = serializers.StringRelatedField()

    class Meta:
        model = ServiceTask
        fields = [
            "id", "employee", "property", "reservation",
            "description", "start_date", "end_date", "status", "type_service", "completed"
        ]


class IncidentSerializer(serializers.ModelSerializer):
    property = serializers.StringRelatedField()
    reported_by = serializers.StringRelatedField()

    class Meta:
        model = Incident
        fields = [
            "id", "title", "property", "reported_by", "assigned_to",
            "type", "description", "date_reported", "status", "resolution_notes"
        ]


class AdditionalExpenseSerializer(serializers.ModelSerializer):
    property = serializers.StringRelatedField()

    class Meta:
        model = AdditionalExpense
        fields = [
            "id", "property", "expense_type", "amount", "description",
            "occurrence_date", "is_recurring", "recurrence_interval"
        ]


class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = ["id", "name", "role", "phone_number", "hire_date", "is_active"]
        # serializer
        full_name = serializers.CharField(source="user.get_full_name", read_only=True)

# conciergerie/ota_webhooks/serializers.py


class AirbnbWebhookSerializer(serializers.Serializer):
    """
    Airbnb JSON structure (simplified)
    {
      "reservation_id": "abc123",
      "listing_id": "xyz789",
      "start_date": "2025-10-01",
      "end_date": "2025-10-05",
      "guest": {
          "first_name": "John",
          "last_name": "Doe",
          "email": "john@airbnb.com"
      },
      "number_of_guests": 2,
      "status": "accepted" | "cancelled"
    }
    """
    reservation_id = serializers.CharField()
    listing_id = serializers.CharField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    guest = serializers.DictField()
    number_of_guests = serializers.IntegerField(min_value=1)
    status = serializers.ChoiceField(choices=["accepted", "cancelled", "modified"])

    def validate_guest(self, value):
        if not value.get("email"):
            raise serializers.ValidationError("Guest email required")
        return value


class BookingWebhookSerializer(serializers.Serializer):
    """
    Booking.com JSON (simplified)
    {
      "reservation_id": "12345678",
      "hotel_id": "987654",
      "arrival_date": "2025-10-01",
      "departure_date": "2025-10-05",
      "customer": {
          "first_name": "Jane",
          "last_name": "Roe",
          "email": "jane@example.com"
      },
      "guest_count": 2,
      "status": "new" | "cancelled"
    }
    """
    reservation_id = serializers.CharField()
    hotel_id = serializers.CharField()
    arrival_date = serializers.DateField()
    departure_date = serializers.DateField()
    customer = serializers.DictField()
    guest_count = serializers.IntegerField(min_value=1)
    status = serializers.ChoiceField(choices=["new", "cancelled", "modified"])

    def validate_customer(self, value):
        if not value.get("email"):
            raise serializers.ValidationError("Customer email required")
        return value

# conciergerie/ota_webhooks/serializers.py


class AirbnbWebhookSerializer(serializers.Serializer):
    """
    Airbnb JSON structure (simplified)
    {
      "reservation_id": "abc123",
      "listing_id": "xyz789",
      "start_date": "2025-10-01",
      "end_date": "2025-10-05",
      "guest": {
          "first_name": "John",
          "last_name": "Doe",
          "email": "john@airbnb.com"
      },
      "number_of_guests": 2,
      "status": "accepted" | "cancelled"
    }
    """
    reservation_id = serializers.CharField()
    listing_id = serializers.CharField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    guest = serializers.DictField()
    number_of_guests = serializers.IntegerField(min_value=1)
    status = serializers.ChoiceField(choices=["accepted", "cancelled", "modified"])

    def validate_guest(self, value):
        if not value.get("email"):
            raise serializers.ValidationError("Guest email required")
        return value


class BookingWebhookSerializer(serializers.Serializer):
    """
    Booking.com JSON (simplified)
    {
      "reservation_id": "12345678",
      "hotel_id": "987654",
      "arrival_date": "2025-10-01",
      "departure_date": "2025-10-05",
      "customer": {
          "first_name": "Jane",
          "last_name": "Roe",
          "email": "jane@example.com"
      },
      "guest_count": 2,
      "status": "new" | "cancelled"
    }
    """
    reservation_id = serializers.CharField()
    hotel_id = serializers.CharField()
    arrival_date = serializers.DateField()
    departure_date = serializers.DateField()
    customer = serializers.DictField()
    guest_count = serializers.IntegerField(min_value=1)
    status = serializers.ChoiceField(choices=["new", "cancelled", "modified"])

    def validate_customer(self, value):
        if not value.get("email"):
            raise serializers.ValidationError("Customer email required")
        return value

        
# conciergerie/serializers_dashboard.py


class TinyPropertySerializer(serializers.ModelSerializer):
    class Meta:
        model = Property
        fields = ("id", "name")


class CheckEventSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    property_name = serializers.CharField(source="property.name")
    guest_name = serializers.CharField()
    reservation_status = serializers.CharField()
    platform = serializers.CharField(source="get_platform_display", required=False)
    check_in = serializers.DateTimeField()
    check_out = serializers.DateTimeField()


class ServiceEventSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    property_name = serializers.CharField(source="property.name")
    service_type = serializers.CharField(source="get_type_service_display")
    employee = serializers.CharField(source="employee.name", required=False)
    status = serializers.CharField()
    start_time = serializers.DateTimeField(source="start_date")


class OccupancySerializer(serializers.Serializer):
    day = serializers.DateField()
    rate = serializers.DecimalField(max_digits=5, decimal_places=1)