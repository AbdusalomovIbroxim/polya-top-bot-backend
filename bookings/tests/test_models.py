import pytest
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta

from playgrounds.models import SportVenue
from django.contrib.auth import get_user_model
from bookings.models import Event, EventParticipant, Payment

User = get_user_model()


@pytest.mark.django_db
def test_event_total_rent_and_participant_amount(settings, django_user_model):
    # подготовка: создаём поле с ценой 100000 за час
    venue = SportVenue.objects.create(name="Test Field", price_per_hour=Decimal("100000.00"), capacity=10)
    user = django_user_model.objects.create_user(username="u1", password="pass", telegram_username="t1", phone="998900000000")
    event = Event.objects.create(creator=user, field=venue, game_time=2, rounds=1, is_private=False)
    total_rent = event.get_total_rent()
    assert total_rent == Decimal("200000.00")  # 100k * 2

    # calculate_participant_amount через service
    from bookings.services import calculate_participant_amount
    amount = calculate_participant_amount(event, venue.capacity)
    assert amount == Decimal("20000.00")  # 200k / 10


@pytest.mark.django_db
def test_event_participant_unique_constraint(django_user_model):
    user = django_user_model.objects.create_user(username="u2", password="pass", telegram_username="t2", phone="998900000001")
    venue = SportVenue.objects.create(name="Test Field 2", price_per_hour=Decimal("50000.00"), capacity=6)
    event = Event.objects.create(creator=user, field=venue, game_time=1, rounds=1)
    # добавляем участника дважды
    EventParticipant.objects.create(event=event, user=user)
    with pytest.raises(Exception):
        EventParticipant.objects.create(event=event, user=user)
