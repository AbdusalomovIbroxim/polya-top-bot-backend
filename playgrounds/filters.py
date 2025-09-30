import django_filters
from .models import SportVenue


class SportVenueFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(field_name="price_per_hour", lookup_expr="gte")
    max_price = django_filters.NumberFilter(field_name="price_per_hour", lookup_expr="lte")

    class Meta:
        model = SportVenue
        fields = ["sport_venue_type", "region", "min_price", "max_price"]