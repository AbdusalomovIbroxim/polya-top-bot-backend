from django.db.models import Sum
from .models import Booking, Transaction
from playgrounds.models import SportVenue
from django.db.models import Count
from django.utils.timezone import now, timedelta


def get_financial_summary(owner):
    """
    Возвращает общий оборот и доход по каждой площадке владельца.
    """
    venues = SportVenue.objects.filter(owner=owner)
    summary = (
        Booking.objects.filter(stadium__in=venues, status=Booking.STATUS_CONFIRMED)
        .values("stadium__id", "stadium__name")
        .annotate(total_amount=Sum("amount"))
        .order_by("-total_amount")
    )
    total = sum(item["total_amount"] or 0 for item in summary)
    return {"total_turnover": total, "by_venues": list(summary)}



def get_venue_usage(owner, period="month"):
    """
    Возвращает количество броней по площадкам за выбранный период.
    """
    venues = SportVenue.objects.filter(owner=owner)

    today = now().date()
    if period == "day":
        start = today
    elif period == "week":
        start = today - timedelta(days=7)
    else:  # month
        start = today - timedelta(days=30)

    usage = (
        Booking.objects.filter(stadium__in=venues, created_at__date__gte=start)
        .values("stadium__id", "stadium__name")
        .annotate(total_bookings=Count("id"))
        .order_by("-total_bookings")
    )
    return {"period": period, "usage": list(usage)}



def get_user_activity(owner, period="month"):
    """
    Считает количество уникальных клиентов, которые бронировали у владельца.
    """
    venues = SportVenue.objects.filter(owner=owner)

    today = now().date()
    if period == "day":
        start = today
    elif period == "week":
        start = today - timedelta(days=7)
    else:
        start = today - timedelta(days=30)

    users = (
        Booking.objects.filter(stadium__in=venues, created_at__date__gte=start)
        .values("user")
        .distinct()
    )
    return {"period": period, "unique_customers": users.count()}


