from rest_framework import serializers
from .models import Booking, Transaction
from playgrounds.models import SportVenue


class SportVenuePreviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = SportVenue
        fields = ["id", "name", "image", "sport_venue_type"]



class BookingSerializer(serializers.ModelSerializer):
    stadium = SportVenuePreviewSerializer(read_only=True)

    class Meta:
        model = Booking
        fields = [
            "id",
            "stadium",
            "start_time",
            "end_time",
            "amount",
            "status",
            "payment_method",
            "created_at",
        ]
        read_only_fields = ["id", "status", "created_at", "amount"]


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = "__all__"
