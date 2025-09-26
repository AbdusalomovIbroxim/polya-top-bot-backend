from rest_framework import serializers
from .models import Booking, Transaction
from playgrounds.models import SportVenue


class SportVenuePreviewSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = SportVenue
        fields = ["id", "name", "image", "sport_venue_type"]

    read_only_fields = ["id", "name", "image", "sport_venue_type"]
    
    def get_image(self, obj):
        first_image = obj.images.first()
        return first_image.image.url if first_image else None


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


class BookingCreateSerializer(serializers.ModelSerializer):
    stadium = serializers.PrimaryKeyRelatedField(
        queryset=SportVenue.objects.all()
    )
    start_time = serializers.DateTimeField()
    end_time = serializers.DateTimeField()
    tz = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Booking
        fields = [
            "stadium",
            "start_time",
            "end_time",
            "payment_method",
            "tz",
        ]



class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = "__all__"

