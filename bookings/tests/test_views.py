import pytest
from decimal import Decimal
from django.urls import reverse
from rest_framework.test import APIClient
from playgrounds.models import SportVenue
from django.contrib.auth import get_user_model
from bookings.models import Event, EventParticipant, Payment

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
def test_create_public_event_and_join(api_client, django_user_model):
    user = django_user_model.objects.create_user(username="creator", password="pass", telegram_username="t1", phone="998900000002")
    venue = SportVenue.objects.create(name="FieldA", price_per_hour=Decimal("100000.00"), capacity=6)
    api_client.force_authenticate(user=user)

    # create event
    url = reverse("events-list")
    resp = api_client.post(url, {"field": venue.id, "game_time": 2, "rounds": 1, "is_private": False}, format="json")
    assert resp.status_code == 201
    data = resp.json()
    event_id = data["id"]

    # create second user and join
    user2 = django_user_model.objects.create_user(username="joiner", password="pass", telegram_username="t2", phone="998900000003")
    api_client.force_authenticate(user=user2)
    join_url = reverse("events-join", args=[event_id])
    r = api_client.post(join_url, {}, format="json")
    assert r.status_code == 201
    assert "user_id" in r.json()


@pytest.mark.django_db
def test_duplicate_join_fails(api_client, django_user_model):
    creator = django_user_model.objects.create_user(username="c", password="pass", telegram_username="t3", phone="998900000004")
    venue = SportVenue.objects.create(name="FieldB", price_per_hour=Decimal("50000.00"), capacity=2)
    api_client.force_authenticate(user=creator)
    resp = api_client.post(reverse("events-list"), {"field": venue.id, "game_time": 1, "rounds": 1, "is_private": False}, format="json")
    assert resp.status_code == 201
    event_id = resp.json()["id"]

    # same user tries to join again
    r = api_client.post(reverse("events-join", args=[event_id]), {}, format="json")
    assert r.status_code in (201, 400)  # either created by creator automatically or rejected due unique

    # try duplicate join by another user twice
    user2 = django_user_model.objects.create_user(username="u", password="pass", telegram_username="t4", phone="998900000005")
    api_client.force_authenticate(user=user2)
    r1 = api_client.post(reverse("events-join", args=[event_id]), {}, format="json")
    r2 = api_client.post(reverse("events-join", args=[event_id]), {}, format="json")
    assert r1.status_code == 201
    assert r2.status_code == 400
